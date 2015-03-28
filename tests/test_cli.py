"""
Unittests for gj2ascii CLI
"""


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
from . import EXPECTED_BAD_PROPERTIES_OUTPUT

import fiona
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

    # def test_paginate_with_two_properties(self):
    #     result = self.runner.invoke(cli.main, [
    #         SINGLE_FEATURE_WV_FILE,
    #         '--width', '10',
    #         '--properties', 'NAME,ALAND',
    #         '--iterate', '--no-prompt'
    #     ])
    #     self.assertEqual(result.exit_code, 0)
    #     self.assertTrue(compare_ascii(result.output, EXPECTED_TWO_PROPERTIES_OUTPUT))
