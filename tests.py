#!/usr/bin/env python


"""
Unittests for gj2ascii
"""


import os
import sys
import unittest

from click.testing import CliRunner
import fiona
import numpy as np

import gj2ascii


EXPECTED_POLYGON_20_WIDE = """
FID: All
Min X: 256407.044597
Max X: 260185.464468
Min Y: 4366133.38032
Max Y: 4369446.92893

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
"""


EXPECTED_LINE_20_WIDE = """

FID: 0
Min X: 256848.263169
Max X: 258243.515542
Min Y: 4366582.89106
Max Y: 4369009.9267

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
. . . . . . . . . + . . . . . . . . . +


FID: 1
Min X: 258993.903373
Max X: 259732.566394
Min Y: 4366911.18574
Max Y: 4368963.02746

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
. . . . . . . . . . . . . . . . . . . +


FID: 2
Min X: 258044.193774
Max X: 258923.554514
Min Y: 4367731.92243
Max Y: 4367767.09686

+ + + + + + + + + + + + + + + + + + + +
"""


def test_format_raster():
        fill = 'f'
        value = 'v'
        a = np.array([
            [0, 0, 0],
            [1, 0, 1],
            [1, 1, 1]])
        expected = os.linesep.join(['f f f', 'v f v', 'v v v'])
        actual = gj2ascii._format_rasterized(a, fill=fill, value=value)
        assert np.array_equal(expected.strip(), actual.strip()) is True


class TestCli(unittest.TestCase):

    def setUp(self):
        self.runner = CliRunner()
        self.poly_file= os.path.join('sample-data', 'polygons.geojson')
        self.line_file = os.path.join('sample-data', 'lines.geojson')

    def test_expected(self):

        # Test --crs, --all, and multiple features
        with fiona.open(self.poly_file) as src:
            src_crs = src.crs

        fill = '.'
        value = '+'
        expected_args = {
            EXPECTED_POLYGON_20_WIDE: [
                self.poly_file,
                '--width', 20,
                '--value', value,
                '--fill', fill,
                '--all'
            ],
            EXPECTED_LINE_20_WIDE: [
                '--width', '20',
                '--value', '+',
                '--fill', '.',
                '--no-prompt',
                '--all-touched',
                '--no-prompt',
                self.line_file
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
        result = self.runner.invoke(gj2ascii.main, ['-v toolong', self.poly_file])
        self.assertNotEqual(result.exit_code, 0)
        self.assertEqual(result.exc_info[0], ValueError)

    def test_bad_rasterize_value(self):
        result = self.runner.invoke(gj2ascii.main, ['-f toolong', self.poly_file])
        self.assertNotEqual(result.exit_code, 0)
        self.assertEqual(result.exc_info[0], ValueError)

    def test_header(self):
        result = self.runner.invoke(gj2ascii.main, [self.poly_file, '--width', 20, '--value', '+', '--fill', '.', '--all'])
        fid = None
        x_min = None
        x_max = None
        y_min = None
        y_max = None
        for line in result.output.strip().splitlines():
            if line.startswith('FID:'):
                fid = line.split()[-1]
            elif line.startswith('Min X:'):
                x_min = float(line.split()[-1])
            elif line.startswith('Max X:'):
                x_max = float(line.split()[-1])
            elif line.startswith('Min Y:'):
                y_min = float(line.split()[-1])
            elif line.startswith('Max Y:'):
                y_max = float(line.split()[-1])
            elif None not in (fid, x_min, x_max, y_min, y_max):
                break
        self.assertEqual(fid.lower(), 'all')
        with fiona.open(self.poly_file) as src:
            s_x_min, s_y_min, s_x_max, s_y_max = src.bounds
            self.assertAlmostEqual(s_x_min, x_min, 2)
            self.assertAlmostEqual(s_x_max, x_max, 2)
            self.assertAlmostEqual(s_y_min, y_min, 2)
            self.assertAlmostEqual(s_y_max, y_max, 2)

    def test_different_width(self):
        fill = '+'
        value = '.'
        width = 31
        result = self.runner.invoke(gj2ascii.main,
                                    ['--width', width, self.poly_file, '--fill', fill, '--value', value, '--no-prompt'])
        self.assertEqual(result.exit_code, 0)
        for line in result.output.strip().splitlines():
            if line.startswith((fill, value)):
                self.assertEqual(len(line.strip().split()), width)


if __name__ == '__main__':
    sys.exit(unittest.main())
