"""
Unittests for gj2ascii
"""


import os


# Expected output, file paths, etc. required for tests


def compare_ascii(out1, out2):
    # Zip over two blocks of text and compare each pair of lines
    for o1_line, o2_line in zip(out1.rstrip().splitlines(), out2.rstrip().splitlines()):
        if o1_line.rstrip() != o2_line.rstrip():
            return False
    return True
