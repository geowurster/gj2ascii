#!/usr/bin/env python


"""
Render GeoJSON as ASCII on the commandline.
"""


from __future__ import division

import sys
from io import BytesIO

import affine
import click
import fiona
import numpy as np
import rasterio
from rasterio.features import rasterize
from shapely.geometry import asShape


__version__ = '0.2.0'
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

PY3 = sys.version_info[0] == 3
if not PY3:
    input = raw_input


def _format_rasterized(a, fill, value):

    """
    Prepare a numpy array for printing to the console.

    Parameters
    ----------
    a : array-like object
        Rasterized geometry
    fill : str
        Background value.
    default_value : str
        Geometry fill value.
    """

    a = a.astype(np.str_)
    a = np.char.replace(a, '0', fill)
    a = np.char.replace(a, '1', value)

    with BytesIO() as _a_f:
        np.savetxt(_a_f, a, fmt='%s')
        _a_f.seek(0)
        return _a_f.read().decode("utf-8")


@click.command()
@click.version_option(version=__version__)
@click.argument('infile')
@click.argument('outfile', type=click.File(mode='w'), default='-')
@click.option(
    '-l', '--layer', 'layer_name', metavar='NAME',
    help="Specify input layer for multi-layer datasources."
)
@click.option(
    '-w', '--width', type=click.INT, default=40,
    help="Render geometry with N rows and columns."
)
@click.option(
    '-i', '--iterate', is_flag=True,
    help="Iterate over input features and display each individually."
)
@click.option(
    '-f', '--fill', default=' ', metavar='CHAR',
    help="Fill value for rasterization.  Only 1 character is allowed."
)
@click.option(
    '-v', '--value', default='+', metavar='CHAR',
    help="Default value for rasterization.  Only 1 character is allowed."
)
@click.option(
    '-at', '--all-touched', is_flag=True,
    help="Enable 'all_touched' rasterization."
)
@click.option(
    '--crs', metavar='DEF',
    help="Specify input CRS."
)
@click.option(
    '--no-prompt', is_flag=True,
    help="Print all geometries without pausing in between."
)
def main(infile, outfile, width, layer_name, iterate, fill, value, all_touched, crs, no_prompt):

    """
    Render GeoJSON on the commandline as ASCII.
    """

    # Make sure that fill and value are both only one character long.  Anything else and the output is weird.
    if len(fill) is not 1:
        raise ValueError("Fill value must be 1 character long not %s: `%s'" % (len(fill), fill))
    if len(value) is not 1:
        raise ValueError("Rasterize value must be 1 character long, not %s: `%s'" % (len(value), value))

    open_kwargs = {'layer': layer_name}
    if crs is not None:
        open_kwargs['crs'] = crs

    with fiona.open(infile, **open_kwargs) as src:

        # If we're rendering all the input features wrap them in a list containing a single generator that produces
        # the geometry to save some memory.  Otherwise, just iterate over all the features normally.
        for feat in src if iterate else [(_f['geometry'] for _f in src)]:

            # Compute the height for the entire layer if rendering all, otherwise just compute from the feature
            if iterate:
                _geom = asShape(feat['geometry'])
                x_min, y_min, x_max, y_max = _geom.bounds
            else:
                x_min, y_min, x_max, y_max = src.bounds

            # Compute output height and cell size
            # Some line and point datasources could yield a situation where the height is 0.  Check and adjust.
            x_delta = x_max - x_min
            y_delta = y_max - y_min
            cell_size = x_delta / width
            height = int(y_delta / cell_size)
            if height is 0:
                height += 1
            transform = affine.Affine.from_gdal(*(x_min, cell_size, 0.0, y_max, 0.0, -cell_size))

            # If rending all then the geometries are already wrapped in a generator
            # Otherwise stick the feature's geometry in a list so `rasterize()` has something to iterate over
            if iterate:
                shapes = [feat['geometry']]

            else:
                shapes = feat

            rasterized = rasterize(
                fill=0,
                default_value=1,
                shapes=shapes,
                out_shape=(height, width),
                transform=transform,
                all_touched=all_touched,
                dtype=rasterio.uint8
            )

            # Write the line
            outfile.write("""
FID: {feat_id}
Min X: {x_min}
Max X: {x_max}
Min Y: {y_min}
Max Y: {y_max}

{formatted_array}
""".format(
                feat_id=feat['id'] if iterate else 'All',
                x_min=x_min,
                x_max=x_max,
                y_min=y_min,
                y_max=y_max,
                formatted_array=_format_rasterized(rasterized, fill=fill, value=value)
            ))

            # If not running on python3 this is aliased to raw_input
            if iterate and not no_prompt:
                if input("Press enter for the next geometry or ^C/^D or 'q' to quit...") != '':  # pragma no cover
                    break

    sys.exit(0)


if __name__ == '__main__':  # pragma no cover
    main()
