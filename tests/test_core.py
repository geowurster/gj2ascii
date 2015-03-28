"""
Unittests for gj2ascii._core
"""


from collections import OrderedDict
import os
import unittest
import warnings

import fiona

import gj2ascii
from . import compare_ascii
from . import POLY_FILE
from . import EXPECTED_POLYGON_20_WIDE


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

    def test_deprecated_dict_table(self):
        with warnings.catch_warnings():
            test_dict = OrderedDict((
                ('Field1', None),
                ('__something', 'a string'),
                ('more', 12345),
                ('other', 1.2344566)
            ))
            self.assertEqual(gj2ascii.dict_table(test_dict), gj2ascii.dict2table(test_dict))

    def test_empty_dict(self):
        with self.assertRaises(ValueError):
            gj2ascii.dict2table({})

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
        self.assertEqual(gj2ascii.dict2table(test_dict), expected)


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
            given = gj2ascii.render(src, 15, bbox=src.bounds)
            computed = gj2ascii.render(src, 15)
            # Passing in a generator and not specifying x/y min/max requires the features to be iterated over twice
            # which is a problem because generators cannot be reset.  A backup of the generator should be created
            # automatically and iterated over the second time.
            generator_output = gj2ascii.render((f for f in src), 15)
        self.assertEqual(given, computed, generator_output)

    def test_with_fiona(self):
        with fiona.open(POLY_FILE) as src:
            r = gj2ascii.render(src, width=20, fill='.', value='+', bbox=src.bounds)
            self.assertEqual(EXPECTED_POLYGON_20_WIDE.strip(), r.strip())


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
            next(gj2ascii._core._geometry_extractor([{'type': None}]))

    def test_single_object(self):
        self.assertDictEqual(self.geometry, next(gj2ascii._core._geometry_extractor(self.geometry)))
        self.assertDictEqual(self.feature['geometry'], next(gj2ascii._core._geometry_extractor(self.feature)))
        self.assertDictEqual(
            self.gi_feature.__geo_interface__['geometry'], next(gj2ascii._core._geometry_extractor(self.gi_feature)))
        self.assertDictEqual(self.gi_geometry.__geo_interface__, next(gj2ascii._core._geometry_extractor(self.gi_geometry)))

    def test_multiple_homogeneous(self):
        for item in gj2ascii._core._geometry_extractor((self.geometry, self.geometry, self.geometry)):
            self.assertDictEqual(item, self.geometry)
        for item in gj2ascii._core._geometry_extractor((self.feature, self.feature, self.feature)):
            self.assertDictEqual(item, self.feature['geometry'])
        for item in gj2ascii._core._geometry_extractor((self.gi_geometry, self.gi_geometry, self.gi_geometry)):
            self.assertDictEqual(item, self.gi_geometry.__geo_interface__)
        for item in gj2ascii._core._geometry_extractor((self.gi_feature, self.gi_feature, self.gi_feature)):
            self.assertDictEqual(item, self.gi_feature.__geo_interface__['geometry'])

    def test_multiple_heterogeneous(self):
        input_objects = (self.geometry, self.feature, self.gi_feature, self.gi_geometry)
        expected = (self.geometry, self.feature['geometry'], self.gi_feature.__geo_interface__['geometry'],
                    self.gi_geometry.__geo_interface__)
        for expected, actual in zip(expected, gj2ascii._core._geometry_extractor(input_objects)):
            self.assertDictEqual(expected, actual)


class TestStack(unittest.TestCase):

    def test_standard(self):
        form = lambda x: os.linesep.join([' '.join(line) for line in x])

        l1 = form([['*', '*', '*', '*', '*'],
                   [' ', ' ', '*', ' ', ' '],
                   ['*', '*', ' ', ' ', ' ']]).strip(os.linesep)

        l2 = form([[' ', ' ', ' ', '+', '+'],
                   [' ', '+', ' ', ' ', ' '],
                   [' ', ' ', '+', '+', '+']]).strip(os.linesep)

        eo = form([['*', '*', '*', '+', '+'],
                   ['.', '+', '*', '.', '.'],
                   ['*', '*', '+', '+', '+']]).strip(os.linesep)

        self.assertEqual(gj2ascii.stack([l1, l2], fill='.').strip(os.linesep), eo.strip(os.linesep))

    def test_exceptions(self):
        # Bad fill value
        with self.assertRaises(ValueError):
            gj2ascii.stack([], fill='too-long')

        # Input layers have different dimensions
        with self.assertRaises(ValueError):
            gj2ascii.stack(['1', '1234'])
