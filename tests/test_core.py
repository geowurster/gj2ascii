#!/usr/bin/env python


"""
Unittests for gj2ascii
"""


from __future__ import unicode_literals

from collections import OrderedDict
import os
import sys
import unittest

from click.testing import CliRunner
import fiona

import gj2ascii


POLY_FILE = os.path.join('sample-data', 'polygons.geojson')
LINE_FILE = os.path.join('sample-data', 'lines.geojson')
SINGLE_FEATURE_WV_FILE = os.path.join('sample-data', 'single-feature-WV.geojson')


EXPECTED_POLYGON_20_WIDE = """
. + . . . . . . . . . . . + . . . . . .
. + + + . . . . . . . . . . . . . . . .
. . . + . . . . . . . . . . . . . . . .
. . . . . . . . . . . . . + . . . . . .
. . . . . . . . . + . . . . . . . . . .
. . . . . . . . . + + . . . . . . . . .
. . . . . . . . . + + + + . . . . . . .
. . . . . . . . . . + + + + . . . . . .
. . . . . . . . . . . + + + . . . . + .
+ + + . . . . . . . . . + + . . . + + +
+ + + + . . . . . . . . . . . . + + + +
. . + . . . . . . + . . . . . . . + + .
. . . . . . . . + + . . . . . . . . + .
. . . . . . . + + + . . . . . . . . + .
. . . . . . + + + + . . . . . . . . . .
. . . . . . + + + + . . . . . . . . . .
. . . . . . . . + + . . . . . . . . . .

""".strip()


EXPECTED_LINE_20_WIDE = """
. . . . . . . . + + + + + + + + + + . .
+ + + + + + + + + . . . . . . . . . . .
+ + . . . . . . . . . . . . . . . . . .
. + + . . . . . . . . . . . . . . . . .
. . + + . . . . . . . . . . . . . . . .
. . . + + + . . . . . . . . . . . . . .
. . . . . + + . . . . . . . . . . . . .
. . . . . . + + . . . . . . . . . . . .
. . . . . . . + + . . . . . . . . . . .
. . . . . . . . + + + . . . . . . . . .
. . . . . . . . . . + + . . . . . . . .
. . . . . . . . . . + . . . . . . . . .
. . . . . . . . . + + . . . . . . . . .
. . . . . . . . + + . . . . . . . . . .
. . . . . . . . + . . . . . . . . . . .
. . . . . . . + + . . . . . . . . . . .
. . . . . . + + . . . . . . . . . . . .
. . . . . + + . . . . . . . . . . . . .
. . . . . + . . . . . . . . . . . . . .
. . . . + + . . . . . . . . . . . . . .
. . . + + . . . . . . . . . . . . . . .
. . . + . . . . . . . . . . . . . . . .
. . + + . . . . . . . . . . . . . . . .
. + + . . . . . . . . . . . . . . . . .
. + . . . . . . . . + . . . . . . . . .
. + + . . . . . . . + + . . . . . . . .
. . + . . . . . . . + + + . . . . . . .
. . + + . . . . . . + . + + . . . . . .
. . . + + . . . . . + . . + + . . . . .
. . . . + + . . . . + . . . + + . . . .
. . . . . + + . . . + . . . . + + . . .
. . . . . . + + . . + . . . . . + + . .
. . . . . . . + + . + . . . . . . + + .
. . . . . . . . + + + . . . . . . . + +


+ . . . . . . . . . . . . . . . . . . .
+ . . . . . . . . . . . . . . . . . . .
+ + . . . . . . . . . . . . . . . . . .
. + . . . . . . . . . . . . . . . . . .
. + . . . . . . . . . . . . . . . . . .
. + + . . . . . . . . . . . . . . . . .
. . + . . . . . . . . . . . . . . . . .
. . + . . . . . . . . . . . . . . . . .
. . + + . . . . . . . . . . . . . . . .
. . . + . . . . . . . . . . . . . . . .
. . . + . . . . . . . . . . . . . . . .
. . . + + . . . . . . . . . . . . . . .
. . . . + . . . . . . . . . . . . . . .
. . . . + + . . . . . . . . . . . . . .
. . . . . + . . . . . . . . . . . . . .
. . . . . + . . . . . . . . . . . . . .
. . . . . + + . . . . . . . . . . . . .
. . . . . . + . . . . . . . . . . . . .
. . . . . . + . . . . . . . . . . . . .
. . . . . . + + . . . . . . . . . . . .
. . . . . . . + . . . . . . . . . . . .
. . . . . . . + . . . . . . . . . . . .
. . . . . . . + + . . . . . . . . . . .
. . . . . . . . + . . . . . . . . . . .
. . . . . . . . + + . . . . . . . . . .
. . . . . . . . . + . . . . . . . . . .
. . . . . . . . . + . . . . . . . . . .
. . . . . . . . . + + . . . . . . . . .
. . . . . . . . . . + . . . . . . . . .
. . . . . . . . . . + . . . . . . . . .
. . . . . . . . . . + + . . . . . . . .
. . . . . . . . . . . + . . . . . . . .
. . . . . . . . . . . + . . . . . . . .
. . . . . . . . . . . + + . . . . . . .
. . . . . . . . . . . . + . . . . . . .
. . . . . . . . . . . . + . . . . . . .
. . . . . . . . . . . . + + . . . . . .
. . . . . . . . . . . . . + . . . . . .
. . . . . . . . . . . . . + + . . . . .
. . . . . . . . . . . . . . + . . . . .
. . . . . . . . . . . . . . + . . . . .
. . . . . . . . . . . . . . + + . . . .
. . . . . . . . . . . . . . . + . . . .
. . . . . . . . . . . . . . . + . . . .
. . . . . . . . . . . . . . . + + . . .
. . . . . . . . . . . . . . . . + . . .
. . . . . . . . . . . . . . . . + . . .
. . . . . . . . . . . . . . . . + + . .
. . . . . . . . . . . . . . . . . + . .
. . . . . . . . . . . . . . . . . + + .
. . . . . . . . . . . . . . . . . . + .
. . . . . . . . . . . . . . . . . . + .
. . . . . . . . . . . . . . . . . . + +
. . . . . . . . . . . . . . . . . . . +
. . . . . . . . . . . . . . . . . . . +


+ + + + + + + + + + + + + + + + + + + +
""".strip()


EXPECTED_ALL_PROPERTIES_OUTPUT = """

+----------+----------------+
| STATEFP  |             54 |
| COUNTYFP |            001 |
| COUNTYNS |       01696996 |
| GEOID    |          54001 |
| NAME     |        Barbour |
| NAMELSAD | Barbour County |
| LSAD     |             06 |
| CLASSFP  |             H1 |
| MTFCC    |          G4020 |
| CSAFP    |           None |
| CBSAFP   |           None |
| METDIVFP |           None |
| FUNCSTAT |              A |
| ALAND    |      883338808 |
| AWATER   |        4639183 |
| INTPTLAT |    +39.1397248 |
| INTPTLON |   -079.9969466 |
+----------+----------------+



      + + +   + + +
    + + + + + +
+ + + + + +
+ + + + +
""".strip()


EXPECTED_TWO_PROPERTIES_OUTPUT = """
+-------+-----------+
| NAME  |   Barbour |
| ALAND | 883338808 |
+-------+-----------+



      + + +   + + +
    + + + + + +
+ + + + + +
+ + + + +
""".strip()


EXPECTED_BAD_PROPERTIES_OUTPUT = """

Couldn't generate attribute table - invalid properties: bad-name



      + + +   + + +
    + + + + + +
+ + + + + +
+ + + + +


""".strip()


def compare_ascii(out1, out2):
    # Zip over two blocks of text and compare each pari of lines
    for o1_line, o2_line in zip(out1.strip().splitlines(), out2.strip().splitlines()):
        if o1_line.strip() != o2_line.strip():
            return False
    return True


def test_compare_ascii():
    # compare_ascii() is a function that is defined within the unittests and only used for testing
    block = """
    line1
    line2
    something
    a n o t h e r line
    None
    6789.2349
    """
    assert compare_ascii(block, block) is True


class TestDictTable(unittest.TestCase):

    def test_empty_dict(self):
        with self.assertRaises(ValueError):
            gj2ascii.dict_table({})

    def test_with_values(self):
        test_dict = OrderedDict((
            ('Field1', None),
            ('__something', 'a string'),
            ('more', 12345),
            ('other', 1.2344566)
        ))
        expected = """
+-------------+-----------+
| Field1      |      None |
| __something |  a string |
| more        |     12345 |
| other       | 1.2344566 |
+-------------+-----------+
""".strip()
        self.assertEqual(gj2ascii.dict_table(test_dict), expected)


class TestRender(unittest.TestCase):

    def test_exception(self):
        with self.assertRaises(ValueError):
            gj2ascii.render([], None, fill='asdf')
        with self.assertRaises(ValueError):
            gj2ascii.render([], None, value='asdf')
        with self.assertRaises(ValueError):
            gj2ascii.render([], width=-1)

    def test_compare_min_max_given_vs_compute_and_as_generator(self):
        # Easiest to compare these 3 things together since they are related
        with fiona.open(POLY_FILE) as src:
            min_max = dict(zip(('x_min', 'y_min', 'x_max', 'y_max'), src.bounds))
            given = gj2ascii.render(src, 15, **min_max)
            computed = gj2ascii.render(src, 15)
            # Passing in a generator and not specifying x/y min/max requires the features to be iterated over twice
            # which is a problem because generators cannot be reset.  A backup of the generator should be created
            # automatically and iterated over the second time.
            generator_output = gj2ascii.render((f for f in src), 15)
        self.assertEqual(given, computed, generator_output)

    def test_with_fiona(self):
        with fiona.open(POLY_FILE) as src:
            kwargs = dict(zip(('x_min', 'y_min', 'x_max', 'y_max'), src.bounds))
            r = gj2ascii.render(src, width=20, fill='.', value='+', **kwargs)
            self.assertEqual(EXPECTED_POLYGON_20_WIDE.strip(), r.strip())


class TestCli(unittest.TestCase):

    def setUp(self):
        self.runner = CliRunner()

    def test_expected(self):

        # Test --crs, --all, and multiple features
        with fiona.open(POLY_FILE) as src:
            src_crs = src.crs

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
                '--value', '+',
                '--fill', '.',
                '--no-prompt',
                '--all-touched',
                '--iterate',
                LINE_FILE
            ]
        }
        for EXPECTED, args in expected_args.items():
            for crs in (None, src_crs):
                if src_crs is not None:
                    args += ['--crs', crs]
                result = self.runner.invoke(gj2ascii.main, args)
                self.assertEqual(result.exit_code, 0)
                expected_lines = EXPECTED.strip().splitlines()
                actual_lines = result.output.strip().splitlines()
                for e_line, a_line in zip(expected_lines, actual_lines):
                    if e_line.startswith((fill, value)) and a_line.startswith((fill, value)):
                        self.assertEqual(e_line.strip().lower(), a_line.strip().lower())

    def test_bad_fill_value(self):
        result = self.runner.invoke(gj2ascii.main, ['-v toolong', POLY_FILE])
        self.assertNotEqual(result.exit_code, 0)
        self.assertTrue(result.output.startswith('ERROR') and
                        'exception' in result.output and 'ValueError' in result.output and 'Value' in result.output)

    def test_bad_rasterize_value(self):
        result = self.runner.invoke(gj2ascii.main, ['-f toolong', POLY_FILE])
        self.assertNotEqual(result.exit_code, 0)
        self.assertTrue(result.output.startswith('ERROR') and
                        'exception' in result.output and 'ValueError' in result.output and 'Fill' in result.output)

    def test_different_width(self):
        fill = '+'
        value = '.'
        width = 31
        result = self.runner.invoke(gj2ascii.main,
                                    ['--width', width, POLY_FILE, '--fill', fill, '--value', value, '--no-prompt'])
        self.assertEqual(result.exit_code, 0)
        for line in result.output.strip().splitlines():
            if line.startswith((fill, value)):
                self.assertEqual(len(line.strip().split()), width)

    def test_paginate_with_all_properties(self):
        result = self.runner.invoke(gj2ascii.main, [
            SINGLE_FEATURE_WV_FILE,
            '--width', '10',
            '--properties', '%all',
            '--iterate', '--no-prompt'
        ])
        self.assertEqual(result.exit_code, 0)
        self.assertTrue(compare_ascii(result.output, EXPECTED_ALL_PROPERTIES_OUTPUT))

    def test_paginate_with_two_properties(self):
        result = self.runner.invoke(gj2ascii.main, [
            SINGLE_FEATURE_WV_FILE,
            '--width', '10',
            '--properties', 'NAME,ALAND',
            '--iterate', '--no-prompt'
        ])
        self.assertEqual(result.exit_code, 0)
        self.assertTrue(compare_ascii(result.output, EXPECTED_TWO_PROPERTIES_OUTPUT))

    def test_bad_property_name_should_still_print_geometry(self):
        result = self.runner.invoke(gj2ascii.main, [
            SINGLE_FEATURE_WV_FILE,
            '--width', '10',
            '--properties', 'bad-name',
            '--iterate', '--no-prompt'
        ])
        self.assertEqual(result.exit_code, 0)
        self.assertTrue(compare_ascii(result.output, EXPECTED_BAD_PROPERTIES_OUTPUT))

    def test_trigger_exception(self):
        result = self.runner.invoke(gj2ascii.main, [
            POLY_FILE,
            '--fill', 'too-wide',
        ])
        self.assertNotEqual(result.exit_code, 0)
        self.assertTrue(
            result.output.startswith('ERROR:') and 'exception' in result.output and 'ValueError' in result.output)


class TestGeometryExtractor(unittest.TestCase):

    def setUp(self):

        class GIFeature(object):
            __geo_interface__ = {
                'type': 'Feature',
                'properties': {},
                'geometry': {
                    'type': 'Point',
                    'coordinates': [10, 20, 30]
                }
            }
        self.gi_feature = GIFeature()

        class GIGeometry(object):
            __geo_interface__ = {
                'type': 'Polygon',
                'coordinates': [[(1.23, -56.5678), (4.897, 20.937), (9.9999999, -23.45)]]
            }
        self.gi_geometry = GIGeometry()

        self.feature = {
            'type': 'Feature',
            'properties': {},
            'geometry': {
                'type': 'Line',
                'coordinates': ((1.23, -67.345), (87.12354, -23.4555), (123.876, -78.9444))
            }
        }

        self.geometry = {
            'type': 'Point',
            'coordinates': (0, 0, 10)
        }

    def test_exceptions(self):
        with self.assertRaises(TypeError):
            next(gj2ascii._geometry_extractor([{'type': None}]))

    def test_single_object(self):
        self.assertDictEqual(self.geometry, next(gj2ascii._geometry_extractor(self.geometry)))
        self.assertDictEqual(self.feature['geometry'], next(gj2ascii._geometry_extractor(self.feature)))
        self.assertDictEqual(
            self.gi_feature.__geo_interface__['geometry'], next(gj2ascii._geometry_extractor(self.gi_feature)))
        self.assertDictEqual(self.gi_geometry.__geo_interface__, next(gj2ascii._geometry_extractor(self.gi_geometry)))

    def test_multiple_homogeneous(self):
        for item in gj2ascii._geometry_extractor((self.geometry, self.geometry, self.geometry)):
            self.assertDictEqual(item, self.geometry)
        for item in gj2ascii._geometry_extractor((self.feature, self.feature, self.feature)):
            self.assertDictEqual(item, self.feature['geometry'])
        for item in gj2ascii._geometry_extractor((self.gi_geometry, self.gi_geometry, self.gi_geometry)):
            self.assertDictEqual(item, self.gi_geometry.__geo_interface__)
        for item in gj2ascii._geometry_extractor((self.gi_feature, self.gi_feature, self.gi_feature)):
            self.assertDictEqual(item, self.gi_feature.__geo_interface__['geometry'])

    def test_multiple_heterogeneous(self):
        input_objects = (self.geometry, self.feature, self.gi_feature, self.gi_geometry)
        expected = (self.geometry, self.feature['geometry'], self.gi_feature.__geo_interface__['geometry'],
                    self.gi_geometry.__geo_interface__)
        for expected, actual in zip(expected, gj2ascii._geometry_extractor(input_objects)):
            self.assertDictEqual(expected, actual)


if __name__ == '__main__':
    sys.exit(unittest.main())
