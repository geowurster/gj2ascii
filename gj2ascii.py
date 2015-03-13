#!/usr/bin/env python


"""
            _ ___                   _ _
   ____ _  (_)__ \ ____ ___________(_|_)
  / __ `/ / /__/ // __ `/ ___/ ___/ / /
 / /_/ / / // __// /_/ (__  ) /__/ / /
 \__, /_/ //____/\__,_/____/\___/_/_/
/____/___/

Render GeoJSON as ASCII on the commandline.
"""


from __future__ import division

from collections import OrderedDict
import itertools
from io import BytesIO
import os
import sys
from types import GeneratorType

import affine
import click
import fiona
import numpy as np
import rasterio
from rasterio.features import rasterize
from shapely.geometry import asShape


__version__ = '0.3.1'
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


DEFAULT_FILL = ' '
DEFAULT_VALUE = '+'


PY3 = sys.version_info[0] == 3
if not PY3:  # pragma no cover
    input = raw_input
    STR = unicode
    STR_TYPES = (str, unicode)
else:  # pragma no cover
    STR = str
    STR_TYPES = (str)


def dict_table(dictionary):

    """
    Convert a dictionary to an ASCII formatted table.

    Example:

        >>> import gj2ascii
        >>> example_dict = OrderedDict((
        ...     ('ALAND', '883338808'),
        ...     ('AWATER', 639183),
        ...     ('CBSAFP', None),
        ...     ('CLASSFP', 'H1'),
        ...     ('COUNTYFP', '001')
        ... ))
        >>> print(gj2ascii.dict_table(example_dict))
        +----------+-----------+
        | AWATER   |   4639183 |
        | ALAND    | 883338808 |
        | COUNTYFP |       001 |
        | CLASSFP  |        H1 |
        | CBSAFP   |      None |
        +----------+-----------+

    Parameter
    ---------
    dictionary : dict
        Keys are
    """

    if not dictionary:
        raise ValueError("Cannot format table - input dictionary is empty.")

    # Cast everything to a string now so we don't have to do it again later
    dictionary = OrderedDict(((STR(k), STR(v)) for k, v in dictionary.items()))

    # Add two at the end to account for spaces around |
    prop_width = max([len(e) for e in dictionary.keys()])
    value_width = max([len(e) for e in dictionary.values()])

    # Add 2 to the prop/value width to account for the single space padding around the properties and values
    # | Property | Value |
    #  ^        ^ ^     ^
    # We don't need it later so only add it here
    divider = ''.join(['+', '-' * (prop_width + 2), '+', '-' * (value_width + 2), '+'])
    output = [divider]
    for prop, value in dictionary.items():
        value = STR(value)
        prop_content = prop + ' ' * (prop_width - len(prop))
        value_content = ' ' * (value_width - len(value)) + value
        output.append('| ' + prop_content + ' | ' + value_content + ' |')

    # Add trailing divider
    output.append(divider)
    return os.linesep.join(output)


def render(ftrz, width, fill=DEFAULT_FILL, value=DEFAULT_VALUE, all_touched=False,
           x_min=None, x_max=None, y_min=None, y_max=None):

    """
    Convert GeoJSON features to their ASCII representation.

    Render all example:

        >>> import gj2ascii
        >>> import fiona
        >>> with fiona.open('sample-data/polygons.geojson') as src:
        ...     print(gj2ascii.render(src, 15, fill='.', value='*'))
        . * . * . . . . . . . . . . .
        . * * . . . . . . * . . . . .
        . . . . . . . . . . . . . . .
        . . . . . . . . . . . . . . .
        . . . . . . . * * . . . . . .
        . . . . . . . * * * . . . . .
        . . . . . . . . * * . . . * .
        * * * . . . . . . . . . * * *
        . * * . . . . . . . . . . * *
        . . . . . . * . . . . . . * .
        . . . . . * * . . . . . . . .
        . . . . . * * . . . . . . . .
        . . . . . . * . . . . . . . .

    Render a single feature:

        >>> import gj2ascii
        >>> import fiona
        >>> with fiona.open('sample-data/polygons.geojson') as src:
        ...     feat = [next(src)]  # Wrap in a list so its iterable
        ...     print(gj2ascii.render(feat, 15, fill='.', value='*'))
                  +
              + +
        + + + + +
        + + + + +               + + +
          + + + + +         + + + +
          + + + + +     + + + + + +
          + + + + + + + + + + + +
              + + + + + + + + + +
                    + + + + + + +
                          + + +


    Parameters
    ----------
    ftrz : iter
        An iterable object producing one GeoJSON feature per iteration.
    width : int
        Number of columns in output ASCII.  A space is inserted between every
        character so the actual output width is `width * 2 - 1`.
    value : str or None, optional
        Render value for polygon pixels.
    fill : str or None, optional
        Render value for non-polygon pixels.
    all_touched : bool, optional
        Fill every 'pixel' the geometries touch instead of every pixel whose
        center intersects the geometry.
    x_min, y_min, x_max, y_max : float, optional
        If reading directly from a large datasource it is advantageous to supply
        these parameters to avoid a potentially large in-memory object and
        expensive computation.  Must supply all or none.

    Returns
    -------
    str
        ASCII representation of input features or array.
    """

    # Values that aren't a string or 1 character wide cause rendering issues
    fill = str(fill)
    value = str(value)
    if len(fill) is not 1:
        raise ValueError("Fill value must be 1 character long, not %s: `%s'" % (len(fill), fill))
    if len(value) is not 1:
        raise ValueError("Rasterize value must be 1 character long, not %s: `%s'" % (len(value), value))

    if x_min is y_min is x_max is y_max is None:

        # If the input is a generator and the min/max values were not supplied we have to compute them from the
        # features, but we need them again later and generators cannot be reset.  This potentially creates a large
        # in-memory object so if processing an entire layer it is best to explicitly define min/max, especially
        # because its also faster.
        if isinstance(ftrz, GeneratorType):
            coord_ftrz, ftrz = itertools.tee(ftrz)
        else:
            coord_ftrz = ftrz
        coords = list(itertools.chain(*[asShape(f['geometry']).bounds for f in coord_ftrz]))
        x_min = min(coords[0::4])
        y_min = min(coords[1::4])
        x_max = max(coords[2::4])
        y_max = max(coords[3::4])

    x_delta = x_max - x_min
    y_delta = y_max - y_min
    cell_size = x_delta / width
    height = int(y_delta / cell_size)
    if height is 0:
        height = 1

    output_array = rasterize(
        fill=0,
        default_value=1,
        shapes=(f['geometry'] for f in ftrz),
        out_shape=(height, width),
        transform=affine.Affine.from_gdal(*(x_min, cell_size, 0.0, y_max, 0.0, -cell_size)),
        all_touched=all_touched,
        dtype=rasterio.uint8
    )

    # Convert to string dtype and do character replacements
    output_array = output_array.astype(np.str_)
    if fill is not None and fill != '0':
        output_array = np.char.replace(output_array, '0', fill)
    if value is not None and fill != '1':
        output_array = np.char.replace(output_array, '1', value)

    # np.savetxt must write to a file-like object so write and immediately read
    # Decode bytes to string and remove the trailing newline character that numpy adds
    with BytesIO() as _a_f:
        np.savetxt(_a_f, output_array, fmt='%s')
        _a_f.seek(0)
        return _a_f.read().decode("utf-8").strip(os.linesep)


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
    help="Single character for non-geometry pixels."
)
@click.option(
    '-v', '--value', default='+', metavar='CHAR',
    help="Single character for geometry pixels."
)
@click.option(
    '-at', '--all-touched', is_flag=True,
    help="Fill all pixels that intersect a geometry instead of those whose center "
         "intersects a geometry."
)
@click.option(
    '--crs', metavar='DEF',
    help="Specify input CRS."
)
@click.option(
    '--no-prompt', is_flag=True,
    help="Print all geometries without pausing in between."
)
@click.option(
    '-p', '--properties', nargs=1, metavar='PROP,PROP,...',
    help="When iterating over features display the specified properties above "
         "each geometry.  Use `%all` for all."
)
def main(infile, outfile, width, layer_name, iterate, fill, value, all_touched, crs, no_prompt, properties):

    """
    Render GeoJSON on the commandline as ASCII.
    """

    try:
        # If the user wants to print all properties
        if properties not in ('%all', None):
            properties = properties.split(',')

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
            for feat in src if iterate else [(_f for _f in src)]:

                # Explicitly supplying the x/y min/max when possible speeds up `render()` and eliminates an extra
                # potentially large in-memory object
                if iterate:
                    x_min = y_min = x_max = y_max = None
                else:
                    x_min, y_min, x_max, y_max = src.bounds

                # Get attributes table, geometry ASCII, and write
                output = os.linesep  # Blank line between prompt and output
                if iterate and properties:

                    # Given the condition: user views entire layer and specifies properties, the properties flag is
                    # silently ignored and the
                    try:
                        if properties == '%all':
                            properties = feat['properties']
                        output += dict_table(
                            OrderedDict(((k, v) for k, v in feat['properties'].items() if k in properties)))
                    except ValueError:
                        output += "Couldn't generate attribute table - invalid properties: %s" % ','.join(properties)
                    # First is to move the cursor from the end of the table to the next line
                    output += os.linesep + os.linesep

                output += render(
                    [feat] if iterate else feat, width,
                    value=value,
                    fill=fill,
                    all_touched=all_touched,
                    x_min=x_min, y_min=y_min,
                    x_max=x_max, y_max=y_max
                ) + os.linesep

                outfile.write(output + os.linesep)

                # If not running on python3 this is aliased to raw_input
                if iterate and not no_prompt:
                    if input("Press enter for the next geometry or ^C/^D or 'q' to quit...") != '':  # pragma no cover
                        break
        sys.exit(0)
    except Exception as e:
        click.echo("ERROR: Encountered an exception - %s" % repr(e), err=True)
        sys.exit(1)
