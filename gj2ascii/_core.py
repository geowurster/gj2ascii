"""
Core components for gj2ascii
"""


from __future__ import division

from collections import OrderedDict
import itertools
from io import BytesIO
import os
import sys
from types import GeneratorType
import warnings

import affine
import numpy as np
import rasterio
from rasterio.features import rasterize
from shapely.geometry import asShape
from shapely.geometry import mapping


__all__ = ['render', 'dict2table', 'dict_table', 'paginate', 'DEFAULT_WIDTH', 'DEFAULT_FILL', 'DEFAULT_VALUE']


DEFAULT_FILL = ' '
DEFAULT_VALUE = '+'
DEFAULT_WIDTH = 40
DEFAULT_RAMP = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '*', '#', '@', '0', '=', '-', '%', '$']


if not sys.version_info[0] >= 3:  # pragma no cover
    STR = unicode
    STR_TYPES = (str, unicode)
    zip_longest = itertools.zip_longest
else:  # pragma no cover
    STR = str
    STR_TYPES = (str)
    zip_longest = itertools.izip_longest


def dict2table(dictionary):

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
        >>> print(gj2ascii.dict2table(example_dict))
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
    # +----------+-------+
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


def dict_table(*args):

    """
    Deprecated alias for `dict2table()`.  Will be removed before 1.0.
    """

    warnings.warn("Function `dict_table()` is deprecated and will be removed "
                  "before 1.0 - use `dict2table()` instead.")

    return dict2table(*args)


def _geometry_extractor(ftrz):

    """
    A generator that yields GeoJSON geometry objects extracted from various
    input types.

    Parameters
    ----------
    ftrz : dict or iterator
        Can be a single GeoJSON feature, geometry, object with a `__geo_interface__`
        method, or an iterable producing one of those types per iteration.

    Yields
    ------
    dict
        A GeoJSON geometry.

    Raises
    ------
    TypeError
        Geometry could not be extracted from an input object.
    """

    if isinstance(ftrz, dict) or hasattr(ftrz, '__geo_interface__'):
        ftrz = [ftrz]
    for obj in ftrz:
        if hasattr(obj, '__geo_interface__'):
            obj = mapping(obj)
        if obj['type'] == 'Feature':
            yield obj['geometry']
        elif 'coordinates' in obj:
            yield obj
        else:
            raise TypeError("An input object isn't a feature, geometry, or object supporting __geo_interface__")


def stack(rendered_layers, values=DEFAULT_RAMP, fill=None):

    if len(rendered_layers) > len(rendered_layers):
        raise ValueError("Received %s layers but only %s values" % (len(rendered_layers), len(values)))

    for rows in zip_longest(*[_l.splitlines() for _l in rendered_layers]):
        if None in rows:
            raise ValueError("Input layers have differing shapes")

    output = []
    for row in zip(*[_l.splitlines() for _l in rendered_layers]):
        o_row = []
        for chars in zip(*row):
            f = [_c for _c in chars if _c != ' ']
            o_row.append(f[-1] if len(f) is not 0 else ' ')
        output.append(''.join(o_row))

    return os.linesep.join(output)


def render(ftrz, width=DEFAULT_WIDTH, fill=DEFAULT_FILL, value=DEFAULT_VALUE, all_touched=False,
           x_min=None, x_max=None, y_min=None, y_max=None):

    """
    Convert GeoJSON features, geometries, or objects supporting `__geo_interface__`
    to their ASCII representation.

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
        ...     print(gj2ascii.render(next(src), 15, fill='.', value='*'))
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
    ftrz : dict or iterator
        Can be a single GeoJSON feature, geometry, object with a `__geo_interface__`
        method, or an iterable producing one of those types per iteration.
    width : int
        Number of columns in output ASCII.  A space is inserted between every
        character so the actual output width is `(width * 2) - 1`.
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
    if width <= 0:
        raise ValueError("Invalid width `%s' - must be > 0" % width)

    if x_min is y_min is x_max is y_max is None:

        # If the input is a generator and the min/max values were not supplied we have to compute them from the
        # features, but we need them again later and generators cannot be reset.  This potentially creates a large
        # in-memory object so if processing an entire layer it is best to explicitly define min/max, especially
        # because its also faster.
        if isinstance(ftrz, GeneratorType):
            coord_ftrz, ftrz = itertools.tee(ftrz)
        else:
            coord_ftrz = ftrz
        coords = list(itertools.chain(*[asShape(g).bounds for g in _geometry_extractor(coord_ftrz)]))
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
        shapes=(g for g in _geometry_extractor(ftrz)),
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


def paginate(ftrz, properties=None, **kwargs):

    """
    Generator to create paginated output for individual features - also handles
    attribute table formatting via the `properties` argument.  Primarily used
    by the CLI.

    Properties
    ----------
    ftrz : dict or iterator
        Anything accepted by `render()`.
    properties : list or None, optional
        Display a table with the specified properties above the geometry.
    kwargs : **kwargs, optional
        Additional keyword arguments for `render()`.

    Yields
    ------
    str
        One feature (with attribute table if specified) as ascii.
    """

    for item in ftrz:

        output = []

        if properties is not None:
            output.append(
                dict2table(OrderedDict((p, item['properties'][p]) for p in properties)))

        output.append(render(item, **kwargs))

        yield os.linesep.join(output) + os.linesep


