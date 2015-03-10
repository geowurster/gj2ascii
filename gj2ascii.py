#!/usr/bin/env python


import os
import sys

import affine
import click
import fiona
import numpy as np
from rasterio.features import rasterize
from shapely.geometry import asShape


__version__ = '0.1'
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


def _geom_generator(feat_iterator):

    """
    Generator to extract geometry from every input feature to conserve memory.

    Parameters
    ----------
    feat_iterator : iter
        An iterable object producing one GeoJSON feature (or anything with a
        'geometry' key) per iteration.

    Yields
    ------
    dict
        GeoJSON geometry object.
    """

    for feat in feat_iterator:
        yield feat['geometry']


def _format_rasterized(a, fill, default_value):

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
    return np.char.replace(a, '1', default_value)


@click.command()
@click.version_option(version=__version__)
@click.argument('infile')
@click.argument('outfile', type=click.File(mode='w'), default='-')
@click.option(
    '-l', '--layer', 'layer_name', metavar='NAME',
    help="Specify input layer for multi-layer datasources."
)
@click.option(
    '-r', '--res', type=click.INT, default=40,
    help="Render geometry with N rows and columns."
)
@click.option(
    '--all', 'render_all', is_flag=True,
    help="Render entire layer instead of individual geometries."
)
@click.option(
    '-f', '--fill', default='', metavar='CHAR',
    help="Fill value for rasterization."
)
@click.option(
    '-d', '--default-value', default='#', metavar='CHAR',
    help="Default value for rasterization."
)
@click.option(
    '-at', '--all-touched', is_flag=True,
    help="Enable 'all_touched' rasterization."
)
def main(infile, outfile, res, layer_name, render_all, fill, default_value, all_touched):

    """
    Render GeoJSON on the commandline as ASCII.

    Use --all to view the entire input layer, otherwise input geometries are
    'paginated' and presented sequentially.  Press enter to advance to the
    next geometry.
    """

    # Rasterize all features in the input layer
    if render_all:
        with fiona.open(infile, layer=layer_name) as vector:

            # Compute cell size for the affine transformation
            x_min, y_min, x_max, y_max = vector.bounds
            cell_size_x = (x_max - x_min) / res
            cell_size_y = (y_max - y_min) / res

            # Burn all geometries into a numpy array
            rasterized = rasterize(
                fill=0,
                default_value=1,
                shapes=_geom_generator(vector),
                out_shape=(res, res),
                transform=affine.Affine(cell_size_x, 0, x_min, 0, -cell_size_y, y_max),
                all_touched=all_touched,
                dtype=np.uint8
            )

            # Print out some stats
            sys.stdout.write(os.linesep)
            sys.stdout.write("Min X: %s" % x_min + os.linesep)
            sys.stdout.write("Max X: %s" % x_max + os.linesep)
            sys.stdout.write("Min Y: %s" % y_min + os.linesep)
            sys.stdout.write("Max Y: %s" % y_max + os.linesep)
            sys.stdout.write(os.linesep)

            # Dump the numpy array
            np.savetxt(outfile, _format_rasterized(rasterized, fill=fill, default_value=default_value), fmt='%s')
            sys.stdout.write(os.linesep)

    # Paginate through
    else:
        with fiona.open(infile, layer=layer_name) as vector:
            for feat in vector:

                # Compute cell size for the affine transformation
                # TODO: Replace with manual computation to eliminate the shapely dependency?
                geom = asShape(feat['geometry'])
                x_min, y_min, x_max, y_max = geom.bounds
                cell_size_x = (x_max - x_min) / res
                cell_size_y = (y_max - y_min) / res

                # Rasterize a geometry
                rasterized = rasterize(
                    fill=0,
                    default_value=1,
                    shapes=[geom],
                    out_shape=(res, res),
                    transform=affine.Affine(cell_size_x, 0, x_min, 0, -cell_size_y, y_max),
                    all_touched=all_touched,
                    dtype=np.uint8
                )

                # Print some stats for the current geometry
                sys.stdout.write(os.linesep)
                sys.stdout.write("FID: %s" % feat['id'] + os.linesep)
                sys.stdout.write("Min X: %s" % x_min + os.linesep)
                sys.stdout.write("Max X: %s" % x_max + os.linesep)
                sys.stdout.write("Min Y: %s" % y_min + os.linesep)
                sys.stdout.write("Max Y: %s" % y_max + os.linesep)

                # Dump the numpy array for the current geometry
                sys.stdout.write(os.linesep)
                np.savetxt(outfile, _format_rasterized(rasterized, fill=fill, default_value=default_value), fmt='%s')
                sys.stdout.write(os.linesep)

                #
                if raw_input("Press enter for the next geometry or 'q' to quit...") != '':
                    break

    sys.exit(0)


if __name__ == '__main__':
    main()
