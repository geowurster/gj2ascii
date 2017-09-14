"""
Unittests for gj2ascii CLI
"""


from __future__ import division

import os
import tempfile
import unittest

import click
import emoji
import fiona as fio
import pytest

import gj2ascii
from gj2ascii import cli


def test_complex(runner, expected_line_40_wide, line_file, compare_ascii):
    result = runner.invoke(cli.main, [
        line_file,
        '--width', '40',
        '--char', '+',
        '--fill', '.',
        '--no-prompt',
        '--all-touched',
        '--iterate',
        '--crs', 'EPSG:26918'
    ])
    assert result.exit_code == 0
    assert compare_ascii(result.output, expected_line_40_wide)


def test_bad_fill_value(runner, poly_file):
    result = runner.invoke(cli.main, ['-c toolong', poly_file])
    assert result.exit_code != 0
    assert result.output.startswith('Usage:')
    assert 'Error:' in result.output
    assert 'must be a single character' in result.output


def test_bad_rasterize_value(runner, poly_file):
    result = runner.invoke(cli.main, ['-f toolong', poly_file])
    assert result.exit_code != 0
    assert result.output.startswith('Usage:')
    assert 'Error:' in result.output
    assert 'must be a single character' in result.output


def test_render_one_layer_too_many_args(runner, poly_file):
    result = runner.invoke(cli.main, [
        poly_file,
        '--char', '-',
        '--char', '8'
    ])
    assert result.exit_code != 0
    assert result.output.startswith('Error:')
    assert 'number' in result.output
    assert '--char' in result.output


def test_different_width(runner, poly_file):
    fill = '+'
    value = '.'
    width = 62
    result = runner.invoke(cli.main, [
        '--width', width,
        poly_file,
        '--fill', fill,
        '--char', value,
        '--no-prompt'
    ])
    assert result.exit_code == 0
    for line in result.output.rstrip(os.linesep).splitlines():
        if line.startswith((fill, value)):
            assert len(line.rstrip(os.linesep).split()) == width / 2


def test_iterate_wrong_arg_count(runner, poly_file):
    result = runner.invoke(cli.main, [
        poly_file,
        '--iterate',
        '--char', '1',
        '--char', '2'
    ])
    assert result.exit_code != 0
    assert result.output.startswith('Error:')
    assert 'arg' in result.output
    assert 'layer' in result.output


def test_bbox(runner, poly_file, small_aoi_poly_line_file, compare_ascii):
    expected = os.linesep.join([
        '                                + + + +',
        '                                  + + +',
        '                                    + +',
        '                                      +',
        '+ +',
        '+ + +',
        '+ + +',
        '+ +',
        '+ +                         +',
        '                          + +',
        '                        + + +',
        '                      + + + +',
        '                    + + + + +',
        '                  + + + + + +',
        '                + + + + + + +',
        ''
    ])
    with fio.open(small_aoi_poly_line_file) as src:
        cmd = [
            poly_file,
            '--width', '40',
            '--char', '+',
            '--bbox',
        ] + list(map(str, src.bounds))
        result = runner.invoke(cli.main, cmd)
    assert result.exit_code == 0
    assert compare_ascii(result.output.strip(), expected.strip())


def test_exceed_auto_generate_colormap_limit(runner, poly_file):
    infiles = [poly_file for i in range(len(gj2ascii.ANSI_COLORMAP.keys()) + 2)]
    result = runner.invoke(cli.main, infiles)
    assert result.exit_code != 0
    assert result.output.startswith('Error:')
    assert 'auto' in result.output
    assert 'generate' in result.output
    assert '--char' in result.output


def test_default_char_map(runner, poly_file, compare_ascii):
    with fio.open(poly_file) as src:
        expected = gj2ascii.render(src)
    result = runner.invoke(cli.main, [
        poly_file
    ])
    assert result.exit_code == 0
    assert compare_ascii(result.output.strip(), expected.strip())


def test_same_char_twice(runner, poly_file, line_file, compare_ascii):
    width = 40
    fill = '.'
    char = '+'
    with fio.open(poly_file) as poly, fio.open(line_file) as line:
        coords = list(poly.bounds) + list(line.bounds)
        bbox = (min(coords[0::4]), min(coords[1::4]), max(coords[2::4]), max(coords[3::4]))
        expected = gj2ascii.render_multiple(
            [(poly, char), (line, char)], width=width, fill=fill, bbox=bbox)
        result = runner.invoke(cli.main, [
            poly_file, line_file,
            '--width', width,
            '--char', char,
            '--char', char,
            '--fill', fill
        ])
        assert result.exit_code == 0
        assert compare_ascii(expected, result.output)


def test_iterate_bad_property(runner, single_feature_wv_file):
    result = runner.invoke(cli.main, [
        single_feature_wv_file,
        '--iterate',
        '--properties', 'bad-prop'
    ])
    assert result.exit_code != 0
    assert isinstance(result.exception, KeyError)


def test_styled_write_to_file(runner, single_feature_wv_file, compare_ascii):
    with fio.open(single_feature_wv_file) as src:
        expected = gj2ascii.render(src, width=20, char='1', fill='0')
    with tempfile.NamedTemporaryFile('r+') as f:
        result = runner.invoke(cli.main, [
            single_feature_wv_file,
            '--width', '20',
            '--properties', 'NAME,ALAND',
            '--char', '1=red',
            '--fill', '0=blue',
            '--outfile', f.name
        ])
        f.seek(0)
        assert result.exit_code == 0
        assert result.output == ''
        assert compare_ascii(f.read().strip(), expected.strip())


def test_stack_too_many_args(runner, multilayer_file):
    result = runner.invoke(cli.main, [
        multilayer_file + ',polygons,lines',
        '--char', '+',
        '--char', '8',
        '--char', '0'  # 2 layers but 3 values
    ])
    assert result.exit_code != 0
    assert result.output.startswith('Error:')
    assert '--char' in result.output
    assert 'number' in result.output
    assert 'equal' in result.output


def test_iterate_too_many_layers(runner, multilayer_file):
    result = runner.invoke(cli.main, [
        multilayer_file,
        '--iterate', '--no-prompt'
    ])
    assert result.exit_code != 0
    assert result.output.startswith('Error:')
    assert 'single layer' in result.output


def test_multilayer_compute_colormap(runner, multilayer_file, compare_ascii):
    coords = []
    for layer in ('polygons', 'lines'):
        with fio.open(multilayer_file, layer=layer) as src:
            coords += list(src.bounds)
    bbox = min(coords[0::4]), min(coords[1::4]), max(coords[2::4]), max(coords[3::4])

    rendered_layers = []
    for layer, char in zip(('polygons', 'lines'), ('0', '1')):
        with fio.open(multilayer_file, layer=layer) as src:
            rendered_layers.append(
                gj2ascii.render(src, width=20, fill=' ', char=char, bbox=bbox))
    expected = gj2ascii.stack(rendered_layers)

    # Explicitly define since layers are not consistently listed in order
    result = runner.invoke(cli.main, [
        multilayer_file + ',polygons,lines',
        '--width', '20'
    ])
    assert result.exit_code == 0
    assert compare_ascii(expected.strip(), result.output.strip())


def test_stack_layers(runner, multilayer_file, compare_ascii):
    expected = os.linesep.join([
        '. + . . . . . . . . . . . + . . . . . .',
        '. + + + . . . . . . . . . . . . . . . .',
        '. . 8 8 8 8 8 8 8 . . . . 8 . . . . . .',
        '. . . 8 . . . . . . . . . 8 . . . . . .',
        '. . . . 8 . . . . + . . . . 8 . . . . .',
        '. . . . . 8 . . . + + . . . 8 . . . . .',
        '. . . . . . 8 . . + + + + . 8 . . . . .',
        '. . . . . 8 . . . . + + + + . 8 . . . .',
        '. . . . 8 . . . . . . 8 8 8 . 8 . . + .',
        '+ + + . 8 . . . 8 8 8 . + + . . 8 + + +',
        '+ + + 8 . . . . . . . . . . . . 8 + + +',
        '. . 8 . . . 8 . . + . . . . . . 8 + + .',
        '. . . 8 . . 8 8 + + . . . . . . . 8 + .',
        '. . . . 8 . 8 + 8 + . . . . . . . 8 + .',
        '. . . . 8 8 + + 8 + . . . . . . . . . .',
        '. . . . . 8 + + + 8 . . . . . . . . . .',
        '. . . . . . . . + + . . . . . . . . . .'
    ])
    result = runner.invoke(cli.main, [
        multilayer_file + ',polygons,lines',
        '--char', '+',
        '--char', '8',
        '--fill', '.',
        '--width', '40'
    ])
    assert result.exit_code == 0
    assert compare_ascii(result.output.strip(), expected)


def test_write_to_file(runner, single_feature_wv_file, compare_ascii):
    expected = os.linesep.join([
        '+-------+-----------+',
        '| NAME  |   Barbour |',
        '| ALAND | 883338808 |',
        '+-------+-----------+',
        '* * * * * * * * * *',
        '* * * * * * * * * *',
        '* * * + + + * + + +',
        '* * + + + + + + * *',
        '+ + + + + + * * * *',
        '+ + + + + * * * * *'
    ])
    with tempfile.NamedTemporaryFile('r+') as f:
        result = runner.invoke(cli.main, [
            single_feature_wv_file,
            '--width', '20',
            '--properties', 'NAME,ALAND',
            '--iterate',
            '--fill', '*',
            '--outfile', f.name
            # --no-prompt should automatically happen in this case
        ])
        f.seek(0)
        assert result.exit_code == 0
        assert result.output == ''
        assert compare_ascii(
            f.read().strip(), expected)


@pytest.mark.xfail(
    os.environ.get('TRAVIS', '').lower() == 'true',
    reason='Failing on Travis for an unknown reason.')
def test_paginate_with_all_properties(
        runner, expected_all_properties_output, single_feature_wv_file,
        compare_ascii):
    result = runner.invoke(cli.main, [
        single_feature_wv_file,
        '--width', '20',
        '--properties', '%all',
        '--iterate', '--no-prompt'
    ])
    assert result.exit_code == 0
    assert compare_ascii(result.output, expected_all_properties_output)


@pytest.mark.xfail(
    os.environ.get('TRAVIS', '').lower() == 'true',
    reason='Failing on Travis for an unknown reason.')
def test_paginate_with_two_properties(
        runner, expected_two_properties_output, single_feature_wv_file,
        compare_ascii):
    result = runner.invoke(cli.main, [
        single_feature_wv_file,
        '--width', '20',
        '--fill', '*',
        '--properties', 'NAME,ALAND',
        '--iterate', '--no-prompt'
    ])
    assert result.exit_code == 0
    assert compare_ascii(result.output, expected_two_properties_output)


def test_simple(runner, expected_polygon_40_wide, poly_file, compare_ascii):
    result = runner.invoke(cli.main, [
        poly_file,
        '--width', '40',
        '--char', '+',
        '--fill', '.',
    ])
    assert result.exit_code == 0
    assert compare_ascii(result.output.strip(), expected_polygon_40_wide)


def test_cb_char_and_fill():
    testvals = {
        'a': [('a', None)],
        ('a', 'b'): [('a', None), ('b', None)],
        'black': [(gj2ascii.DEFAULT_COLOR_CHAR['black'], 'black')],
        ('black', 'blue'): [
            (gj2ascii.DEFAULT_COLOR_CHAR['black'], 'black'),
            (gj2ascii.DEFAULT_COLOR_CHAR['blue'], 'blue')
        ],
        ('+=red', '==yellow'): [('+', 'red'), ('=', 'yellow')],
        None: []
    }

    # The callback can return a list of tuples or a list of lists.  Force test to compare
    # list to list.
    for inval, expected in testvals.items():
        expected = [list(i) for i in expected]
        actual = [list(i) for i in cli._cb_char_and_fill(None, None, inval)]
        assert expected == actual
    with pytest.raises(click.BadParameter):
        cli._cb_char_and_fill(None, None, 'bad-color')
    with pytest.raises(click.BadParameter):
        cli._cb_char_and_fill(None, None, ('bad-color'))


def test_cb_properties():
    for v in ('%all', None):
        assert v == cli._cb_properties(None, None, v)

    props = 'PROP1,PROP2,PROP3'
    assert props.split(',') == cli._cb_properties(None, None, props)


def test_cb_multiple_default():
    values = ('1', '2')
    assert values == cli._cb_multiple_default(None, None, values)
    values = '1'
    assert (values) == cli._cb_multiple_default(None, None, values)


def test_cb_bbox(poly_file):

    with fio.open(poly_file) as src:

        assert None == cli._cb_bbox(None, None, None)
        assert src.bounds == cli._cb_bbox(None, None, src.bounds)

    # Bbox with invalid X values
    with pytest.raises(click.BadParameter):
        cli._cb_bbox(None, None, (2, 0, 1, 0,))

    # Bbox with invalid Y values
    with pytest.raises(click.BadParameter):
        cli._cb_bbox(None, None, (0, 2, 0, 1))

    # Bbox with invalid X and Y values
    with pytest.raises(click.BadParameter):
        cli._cb_bbox(None, None, (2, 2, 1, 1,))


def test_with_emoji(runner, poly_file, line_file):
    result = runner.invoke(cli.main, [
        poly_file,
        line_file,
        '-c', ':water_wave:',
        '-c', ':+1:'
    ])
    assert result.exit_code is 0
    for c in (':water_wave:', ':+1:'):
        ucode = emoji.unicode_codes.EMOJI_ALIAS_UNICODE[c]
        assert ucode in result.output


def test_no_style(runner, expected_polygon_40_wide, poly_file, compare_ascii):
    result = runner.invoke(cli.main, [
        poly_file,
        '-c', '+',
        '--no-style',
        '-w', '40',
        '-f', '.'
    ])
    assert result.exit_code is 0
    assert compare_ascii(result.output.strip(), expected_polygon_40_wide)


def test_print_colors(runner):
    result = runner.invoke(cli.main, [
        '--colors'
    ])
    assert result.exit_code is 0
    for color in gj2ascii.DEFAULT_COLOR_CHAR.keys():
        assert color in result.output
