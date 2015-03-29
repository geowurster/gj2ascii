"""
Unittests for gj2ascii CLI
"""


import tempfile
import unittest

from gj2ascii import cli
from . import compare_ascii
from . import POLY_FILE
from . import LINE_FILE
from . import SINGLE_FEATURE_WV_FILE
from . import EXPECTED_TWO_PROPERTIES_OUTPUT
from . import EXPECTED_ALL_PROPERTIES_OUTPUT
from . import EXPECTED_POLYGON_20_WIDE
from . import EXPECTED_LINE_20_WIDE
from . import MULTILAYER_FILE
from . import EXPECTED_STACKED
from . import EXPECTED_STACK_PERCENT_ALL

import click
from click.testing import CliRunner


class TestCli(unittest.TestCase):

    def setUp(self):
        self.runner = CliRunner()

    def test_expected(self):

        fill = '.'
        value = '+'
        expected_args = {
            EXPECTED_POLYGON_20_WIDE: [
                POLY_FILE,
                '--width', '20',
                '--value', value,
                '--fill', fill,
            ],
            EXPECTED_LINE_20_WIDE: [
                '--width', '20',
                '--value', value,
                '--fill', fill,
                '--no-prompt',
                '--all-touched',
                '--iterate',
                LINE_FILE
            ]
        }
        for EXPECTED, args in expected_args.items():
            for crs in (None, 'EPSG:4326'):
                if crs is not None:
                    args += ['--crs', crs]
                result = self.runner.invoke(cli.main, args)
                self.assertEqual(result.exit_code, 0)
                expected_lines = EXPECTED.strip().splitlines()
                actual_lines = result.output.strip().splitlines()
                for e_line, a_line in zip(expected_lines, actual_lines):
                    if e_line.startswith((fill, value)) and a_line.startswith((fill, value)):
                        self.assertEqual(e_line.strip().lower(), a_line.strip().lower())

    def test_bad_fill_value(self):
        result = self.runner.invoke(cli.main, ['-v toolong', POLY_FILE])
        self.assertNotEqual(result.exit_code, 0)
        self.assertTrue(result.output.startswith('Usage:') and
                        'Error:' in result.output and 'must be a single character' in result.output)

    def test_bad_rasterize_value(self):
        result = self.runner.invoke(cli.main, ['-f toolong', POLY_FILE])
        self.assertNotEqual(result.exit_code, 0)
        self.assertTrue(result.output.startswith('Usage:') and
                        'Error:' in result.output and 'must be a single character' in result.output)

    def test_different_width(self):
        fill = '+'
        value = '.'
        width = 31
        result = self.runner.invoke(cli.main,
                                    ['--width', width, POLY_FILE, '--fill', fill, '--value', value, '--no-prompt'])
        self.assertEqual(result.exit_code, 0)
        for line in result.output.strip().splitlines():
            if line.startswith((fill, value)):
                self.assertEqual(len(line.strip().split()), width)

    def test_paginate_with_all_properties(self):
        result = self.runner.invoke(cli.main, [
            SINGLE_FEATURE_WV_FILE,
            '--width', '10',
            '--properties', '%all',
            '--iterate', '--no-prompt'
        ])
        self.assertEqual(result.exit_code, 0)
        self.assertTrue(compare_ascii(result.output, EXPECTED_ALL_PROPERTIES_OUTPUT))

    def test_paginate_with_two_properties(self):
        result = self.runner.invoke(cli.main, [
            SINGLE_FEATURE_WV_FILE,
            '--width', '10',
            '--properties', 'NAME,ALAND',
            '--iterate', '--no-prompt'
        ])
        self.assertEqual(result.exit_code, 0)
        self.assertTrue(compare_ascii(result.output, EXPECTED_TWO_PROPERTIES_OUTPUT))

    def test_iterate_wrong_arg_count(self):
        result = self.runner.invoke(cli.main, [
            POLY_FILE,
            '--iterate',
            '--value', '1',
            '--value', '1'
        ])
        self.assertNotEqual(result.exit_code, 0)
        self.assertTrue(result.output.startswith('Error:') and 'specified once' in result.output)

    def test_iterate_bad_property(self):
        result = self.runner.invoke(cli.main, [
            SINGLE_FEATURE_WV_FILE,
            '--iterate',
            '--properties', 'bad-prop'
        ])
        self.assertNotEqual(result.exit_code, 0)
        self.assertTrue(result.output.strip(), "Error: KeyError('bad-prop',)")

    def test_write_to_file(self):
        with tempfile.NamedTemporaryFile('r+') as f:
            result = self.runner.invoke(cli.main, [
                SINGLE_FEATURE_WV_FILE,
                '--width', '10',
                '--properties', 'NAME,ALAND',
                '--iterate', '--no-prompt',
                '--outfile', f.name
            ])
            f.seek(0)
            self.assertEqual(result.exit_code, 0)
            self.assertEqual(result.output, '')
            self.assertTrue(compare_ascii(f.read(), EXPECTED_TWO_PROPERTIES_OUTPUT))

    def test_stack_layers(self):
        result = self.runner.invoke(cli.main, [
            MULTILAYER_FILE,
            '--layer', 'polygons',
            '--layer', 'lines',
            '--value', '+',
            '--value', '8',
            '--fill', '.',
            '--width', '20'
        ])
        self.assertEqual(result.exit_code, 0)
        self.assertTrue(compare_ascii(result.output.strip(), EXPECTED_STACKED.strip()))

    def test_stack_too_many_args(self):
        result = self.runner.invoke(cli.main, [
            MULTILAYER_FILE,
            '--layer', 'polygons',
            '--layer', 'lines',
            '--value', '+',
            '--value', '8',
            '--value', '0'  # 2 layers but 3 values
        ])
        self.assertNotEqual(result.exit_code, 0)
        print(result.output)
        self.assertTrue(result.output.startswith('Error:') and
                        'Stacking' in result.output and 'specified only once' in result.output)

    def test_stack_percent_all_layers(self):
        result = self.runner.invoke(cli.main, [
            MULTILAYER_FILE,
            '--layer', '%all',
            '--width', '20'
        ])
        self.assertEqual(result.exit_code, 0)
        self.assertTrue(compare_ascii(result.output.strip(), EXPECTED_STACK_PERCENT_ALL.strip()))

    def test_render_one_layer_too_many_args(self):
        result = self.runner.invoke(cli.main, [
            POLY_FILE,
            '--value', '-',
            '--value', '8'
        ])
        self.assertNotEqual(result.exit_code, 0)
        self.assertTrue(result.output.startswith('Error:') and 'specified once' in result.output)


class TestCallbacks(unittest.TestCase):

    def test_callback_fill_and_value(self):

        # Valid values
        for cb_value in ('a', ('a', 'b', 'c')):
            self.assertEqual(cb_value, cli._callback_fill_and_value(None, None, cb_value))

        # invalid values
        for cb_value in ('too-long', ('abc', 'def')):
            with self.assertRaises(click.BadParameter):
                cli._callback_fill_and_value(None, None, cb_value)

    def test_callback_properties(self):

        for v in ('%all', None):
            self.assertEqual(v, cli._callback_properties(None, None, v))

        props = 'PROP1,PROP2,PROP3'
        self.assertEqual(props.split(','), cli._callback_properties(None, None, props))

    def test_callback_multiple_default(self):

        values = ('1', 2)
        self.assertEqual(values, cli._callback_multiple_default(None, None, values))
        values = '1'
        self.assertEqual((values), cli._callback_fill_and_value(None, None, values))
