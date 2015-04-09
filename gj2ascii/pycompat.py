"""
Python 2/3 compatibility
"""


import itertools
import sys


if sys.version_info[0] >= 3:  # pragma no cover
    string_types = str,
    text_type = str
    zip_longest = itertools.zip_longest
else:  # pragma no cover
    string_types = basestring,
    text_type = unicode
    zip_longest = itertools.izip_longest
