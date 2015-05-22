"""
            _ ___                   _ _
   ____ _  (_)__ \ ____ ___________(_|_)
  / __ `/ / /__/ // __ `/ ___/ ___/ / /
 / /_/ / / // __// /_/ (__  ) /__/ / /
 \__, /_/ //____/\__,_/____/\___/_/_/
/____/___/

Render GeoJSON as ASCII with Python.

    >>> import fiona as fio
    >>> import gj2ascii
    >>> with fio.open('sample-data/polygons.geojson') as poly, \\
    ...         fio.open('sample-data/lines.geojson') as lines, \\
    ...         fio.open('sample-data/small-aoi-polygon-line.geojson') as bbox:
    ...     charmap = [
    ...         (poly, '1'),
    ...         (lines, '0')
    ...     ]
    ...     print(gj2ascii.style_multiple(charmap, 40, fill=' ', bbox=bbox.bounds))
    0 0 0 0 0 0 1 0 0 0 0 0 0 0 0 0 2 2 2 2
    0 0 0 0 0 1 0 0 0 0 0 0 0 0 0 0 0 2 2 2
    0 0 0 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0 1 1
    0 0 0 0 1 0 0 0 0 0 0 0 0 1 1 1 1 1 0 2
    2 2 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
    2 2 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
    2 1 2 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
    2 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
    1 2 0 0 0 0 0 0 1 0 0 0 0 0 2 0 0 0 0 0
    0 1 0 0 0 0 0 0 1 1 0 0 0 2 2 0 0 0 0 0
    0 0 1 0 0 0 0 0 1 0 1 0 2 2 2 0 0 0 0 0
    0 0 0 1 0 0 0 0 1 0 0 1 2 2 2 0 0 0 0 0
    0 0 0 0 1 0 0 1 0 0 2 2 1 2 2 0 0 0 0 0
    0 0 0 0 0 1 0 1 0 2 2 2 2 1 2 0 0 0 0 0
    0 0 0 0 0 0 1 1 2 2 2 2 2 2 1 0 0 0 0 0
"""


from .core import (
    array2ascii, ascii2array, dict2table, min_bbox, paginate, render,
    render_multiple, stack, style, style_multiple
)

from .core import (
    DEFAULT_WIDTH, DEFAULT_FILL, DEFAULT_CHAR, DEFAULT_CHAR_RAMP,
    DEFAULT_CHAR_COLOR, DEFAULT_COLOR_CHAR, ANSI_COLORMAP
)


__version__ = '0.4'
__author__ = 'Kevin Wurster'
__email__ = 'wursterk@gmail.com'
__source__ = 'https://github.com/geowurster/gj2ascii'
__license__ = '''
New BSD License

Copyright (c) 2015, Kevin D. Wurster
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

* The names of its contributors may not be used to endorse or promote products
  derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
'''
