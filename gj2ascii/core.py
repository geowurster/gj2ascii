"""
Core components for gj2ascii
"""


from __future__ import division

from collections import OrderedDict
import itertools
import os
from types import GeneratorType

from .pycompat import text_type

import affine
import numpy as np
import rasterio as rio
from rasterio.features import rasterize
from shapely.geometry import asShape
from shapely.geometry import mapping


__all__ = [
    'render', 'stack', 'style', 'render_multiple', 'style_multiple', 'paginate', 'dict2table',
    'ascii2array', 'array2ascii',
    'DEFAULT_WIDTH', 'DEFAULT_FILL', 'DEFAULT_CHAR', 'DEFAULT_CHAR_RAMP', 'DEFAULT_CHAR_COLOR', 'DEFAULT_COLOR_CHAR',
    'ANSI_COLORMAP',
]


DEFAULT_FILL = ' '
DEFAULT_CHAR = '+'
DEFAULT_WIDTH = 40
DEFAULT_CHAR_RAMP = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '*', '#', '@', '0', '=', '-', '%', '$']
_ANSI_RESET = '\033[0m'
ANSI_COLORMAP = {
    'black': '\x1b[30m\x1b[40m',
    'red': '\x1b[31m\x1b[41m',
    'green': '\x1b[32m\x1b[42m',
    'yellow': '\x1b[33m\x1b[43m',
    'blue': '\x1b[34m\x1b[44m',
    'magenta': '\x1b[35m\x1b[45m',
    'cyan': '\x1b[36m\x1b[46m',
    'white': '\x1b[37m\x1b[47m'
}
DEFAULT_CHAR_COLOR = {
    '0': 'green',
    '1': 'blue',
    '2': 'red',
    '3': 'yellow',
    '4': 'cyan',
    '5': 'magenta',
    '6': 'white',
    '7': 'black'
}
DEFAULT_COLOR_CHAR = {v: k for k, v in DEFAULT_CHAR_COLOR.items()}


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
    dictionary = OrderedDict(((text_type(k), text_type(v)) for k, v in dictionary.items()))

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
        value = text_type(value)
        prop_content = prop + ' ' * (prop_width - len(prop))
        value_content = ' ' * (value_width - len(value)) + value
        output.append('| ' + prop_content + ' | ' + value_content + ' |')

    # Add trailing divider
    output.append(divider)

    return os.linesep.join(output)


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


def ascii2array(ascii):

    """
    Convert an ASCII rendering to an array.  The returned object is not a numpy
    array but can easily be converted with `np.array()`.

    Example input:

        # Rendered ASCII
        * * * * *
          *   *
        * * * * *

        >>> import gj2ascii
        >>> pprint(gj2ascii.ascii2array(rendered_ascii))
        [['*', '*', '*', '*', '*'],
         [' ', '*', ' ', '*', ' '],
         ['*', '*', '*', '*', '*']]

    Parameters
    ---------
    ascii : str
        Rendered ASCII from `render()` or `stack()`.

    Returns
    -------
    list
        A list where each element is a list containing one value per pixel.
    """

    return [list(row[::2]) for row in ascii.splitlines()]


def array2ascii(arr):

    """
    Convert an array to its ASCII rendering.  Designed to take the output from
    `ascii2array()` but will also work on a numpy array.

    Example input:

        # Array
        [['*', '*', '*', '*', '*'],
         [' ', '*', ' ', '*', ' '],
         ['*', '*', '*', '*', '*']]

        >>> import gj2ascii
        >>> pprint(gj2ascii.ascii2array(array))
        * * * * *
          *   *
        * * * * *

    Parameters
    ----------
    arr : str
        Rendered ASCII from `render()` or `stack()`.

    Returns
    -------
    list
        A list where each element is a list containing one value per pixel.
    """

    return os.linesep.join([' '.join(row) for row in arr])


def stack(rendered_layers, fill=DEFAULT_FILL):

    """
    Render a stack of input layers into a single overlapping product.  Layers
    are drawn in order according to the painters algorithm so the first layer
    will be covered by all subsequent layers.

    There are two important requirements for the 'rendered_layers' parameter.
    Each input ASCII rendering must have its fill value set to a single space,
    which is overwritten by the 'fill' parameter here when the layers are
    stacked.

    It is important that all input layers be rendered with the same width and
    bbox to ensure that they actually represent the same spatial area.  It is
    possible to provide input layers whose ASCII representations have a matching
    number of rows and columns even if they do not overlap spatially or were
    produced from different bounding boxes.  The example below shows how to
    ensure proper stackability.

    Example:

        # Rendered layer 1
        0 0 0 0 0
            0
        0 0 0 0 0

        # Rendered layer 2
        1       1

        1       1

        >>> import gj2ascii
        >>> layer1 = gj2ascii.render(geom1, width=5, fill=' ', value='0')
        >>> layer2 = gj2ascii.render(geom2, width=5, fill=' ', value='1')
        >>> layers = [layer1, layer2]
        >>> print(gj2ascii.stack(layers, fill='.'))
        1 0 0 0 1
        . . 0 . .
        1 0 0 0 1

    Parameters
    ----------
    rendered_layers : iterable
        An iterable producing one rendered layer per iteration.  Layers must
        all have the same dimension and must have been rendered with an empty
        space (' ') as the fill value.  Using the same `bbox` and `width` values
        for `render()` when preparing input layers helps ensure layers have
        matching dimensions.
    fill : str, optional
        A new fill value for the rendered stack.  Must be a single character.

    Returns
    -------
    str
        All stacked layers rendered into a single ASCII representation with the
        first input layer on the bottom and the last on top.
    """

    fill = str(fill)
    if len(fill) is not 1:
        raise ValueError("Invalid fill value `%s' - must be 1 character long" % fill)

    output_array = []
    for row_stack in zip(*map(ascii2array, rendered_layers)):

        if len(set((len(_r) for _r in row_stack))) is not 1:
            raise ValueError("Input layers have heterogeneous dimensions")

        o_row = []
        for pixel_stack in zip(*row_stack):
            opaque_pixels = [_p for _p in pixel_stack if _p != ' ']
            if len(opaque_pixels) is 0:
                o_row.append(fill)
            else:
                o_row.append(opaque_pixels[-1])
        output_array.append(o_row)

    return array2ascii(output_array)


def render(ftrz, width=DEFAULT_WIDTH, fill=DEFAULT_FILL, char=DEFAULT_CHAR, all_touched=False, bbox=None):

    """
    Convert GeoJSON features, geometries, or objects supporting `__geo_interface__`
    to their ASCII representation.

    Render an entire layer:

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
        Can be a single GeoJSON feature, geometry, object supporting
        `__geo_interface__`, or an iterable producing one of those types per
        iteration.
    width : int, optional
        Number of columns in output ASCII.  A space is inserted between every
        character so the actual output width is `(width * 2) - 1`.
    char : str or None, optional
        Character to use for pixels touched by a geometry.
    fill : str or None, optional
        character to use for pixels that are not touched by a geometry.
    all_touched : bool, optional
        Fill every pixel the geometries touch instead of every pixel whose
        center intersects the geometry.
    bbox : tuple, optional
        A 4 element tuple consisting of x_min, y_min, x_max, y_max.  Used to
        zoom in on a particular area of interest and if not supplied is computed
        on the fly from all input objects.  If reading from a datasource with a
        large number of features it is advantageous to supply this parameter to
        avoid a potentially large in-memory object and expensive computation.
        If not supplied and the input object is a `fio.Collection()` instance
        the bbox will be automatically computed from the `bounds` property.

    Returns
    -------
    str
        ASCII representation of input features or array.
    """

    # Values that aren't a string or 1 character wide cause rendering issues
    fill = str(fill)
    char = str(char)
    if len(fill) is not 1:
        raise ValueError("Invalid fill value `%s' - must be 1 character long" % fill)
    if len(char) is not 1:
        raise ValueError("Invalid pixel value `%s' - must be 1 character long" % char)
    if width <= 0:
        raise ValueError("Invalid width `%s' - must be > 0" % width)

    # If the input is a generator and the min/max values were not supplied we have to compute them from the
    # features, but we need them again later and generators cannot be reset.  This potentially creates a large
    # in-memory object so if processing an entire layer it is best to explicitly define min/max, especially
    # because its also faster.
    if bbox:
        x_min, y_min, x_max, y_max = bbox
    else:
        _bbox, ftrz = _bbox_from_arbitrary_iterator(ftrz)
        x_min, y_min, x_max, y_max = _bbox

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
        dtype=rio.uint8
    )

    # Convert to string dtype and do character replacements
    output_array = output_array.astype(np.str_)
    if fill is not None and fill != '0':
        output_array = np.char.replace(output_array, '0', fill)
    if char is not None and fill != '1':
        output_array = np.char.replace(output_array, '1', char)

    return array2ascii(output_array)


def paginate(ftrz, properties=None, colormap=None, **kwargs):

    """
    Generator to create paginated output for individual features - also handles
    attribute table formatting via the `properties` argument.  Primarily used
    by the CLI.

    Properties
    ----------
    ftrz : dict or iterator
        Anything accepted by `render()`.
    properties : list, optional
        Display a table with the specified properties above the geometry.
    colormap : dict or None, optional
        If provided the output text will contain color codes.  See `style()`
        for more information.
    kwargs : **kwargs, optional
        Additional keyword arguments for `render()`.

    Yields
    ------
    str
        One feature (with attribute table and colors if specified) as ascii.
    """

    for item in ftrz:

        output = []

        if properties is not None:
            output.append(
                dict2table(OrderedDict((p, item['properties'][p]) for p in properties)))
        r = render(item, **kwargs)
        if not colormap:
            output.append(r)
        else:
            output.append(style(r, colormap=colormap))

        yield os.linesep.join(output) + os.linesep


def style(rendered_ascii, colormap):

    """
    Colorize an ASCII rendering.

    Parameters
    ----------
    rendered_ascii : str
        An ASCII rendering from `render()` or `stack()`.
    colormap : dict
        A dictionary where keys are color names and values are characters
        to which the color will be applied.

    Returns
    -------
    str
        A formatted string containing ANSI codes that is ready for `print()`.
    """

    output = []
    for row in ascii2array(rendered_ascii):
        o_row = []
        for char in row:
            if char in colormap:
                color = ANSI_COLORMAP[colormap[char]]
            else:
                color = ''
            o_row.append(color + char + ' ' + _ANSI_RESET)
        output.append(''.join(o_row))
    return os.linesep.join(output)


def render_multiple(ftr_char_pairs, width=DEFAULT_WIDTH, fill=DEFAULT_FILL, **kwargs):

    """
    A quick way to render multiple layers, features, or geometries without having
    to render each layer individually and combine via `stack()`.  See
    `style_multiple()` for similar functionality but with direct access to colors
    rather than characters.

    A minimum bounding box is computed from all the input objects if one is not
    supplied in the kwargs.  See the 'bbox' parameter in `render()` for more
    information about how this parameter can be used and its performance
    implications.

    Example:

        >>> import gj2ascii
        >>> import fiona as fio
        >>> with fio.open('sample-data/polygons.geojson') as poly:
        ...     with fio.open('sample-data/lines.json') as lines:
        ...         print(gj2ascii.render_multiple([(poly, '0'), (lines, '1')], 10))
                    0
          1 1 1 1   1
            1       1
              1   0 0 1
        0   1   1 1 1 1   0
        0 1   1         1 0
            1 1 1       1
            1 0 1

    Parameters
    ----------
    ftr_char_pairs : list
        A list of tuples where the first element of each tuple is an object
        suitable for `render()` and the second is the ASCII character to use
        when rendering.
    width : int, optional
        See `render()`.
    fill : str, optional
        See `render()`.
    kwargs : **kwargs, optional
        Additional keyword arguments for `render()`.

    Returns
    -------
    str
        All input layers, features, or geometries rendered as ASCII.
    """

    # Render is intended to be used as render(ftrz, width) but if it is expected to only be supplied
    # as a kwarg it might create some confusion.  If the user supplies a value use that instead.
    width = kwargs.pop('width', width)

    if 'bbox' in kwargs:
        bbox = kwargs.pop('bbox')
        iter_pairs = ftr_char_pairs
    else:
        coords = []
        iter_pairs = []
        for ftrz, char in ftr_char_pairs:
            _bbox, _ftrz_copy = _bbox_from_arbitrary_iterator(ftrz)
            coords.append(_bbox)
            iter_pairs.append((_ftrz_copy, char))
        coords = [_i for _i in itertools.chain(*coords)]
        bbox = (min(coords[0::4]), min(coords[1::4]), max(coords[2::4]), max(coords[3::4]))

    rendered_layers = []
    for ftrz, char in iter_pairs:
        rendered_layers.append(render(ftrz, width=width, char=char, bbox=bbox, fill=' ', **kwargs))

    return stack(rendered_layers, fill=fill)


def style_multiple(ftr_color_pairs, fill='black', **kwargs):

    """
    A quick way to render and style multiple layers, features, or geometries
    without having to render each layer individually, combine via `stack()`,
    and apply colors via `style()`.  See `render_multiple()` For similar
    functionality but with direct access to characters rather than colors.

    A minimum bounding box is computed from all the input objects if one is not
    supplied in the kwargs.  See the 'bbox' parameter in `render()` for more
    information about how this parameter can be used and its performance
    implications.

    Example:

        # 7's in the output rendering are blue, 1's are black, and 0's are green
        >>> import gj2ascii
        >>> import fiona as fio
        >>> with fio.open('sample-data/polygons.geojson') as poly:
        ...     with fio.open('sample-data/lines.geojson') as lines:
        ...         input_layers = [(poly, 'blue'), (lines, 'black')]
        ...         print(gj2ascii.style_multiple(input_layers, fill='green', width=10))
        0 0 0 0 0 0 1 0 0 0
        0 7 7 7 7 0 7 0 0 0
        0 0 7 0 0 0 7 0 0 0
        0 0 0 7 0 1 1 7 0 0
        1 0 7 0 7 7 7 7 0 1
        1 7 0 7 0 0 0 0 7 1
        0 0 7 7 7 0 0 0 7 0
        0 0 7 1 7 0 0 0 0 0

    Parameters
    ----------
    ftr_color_pairs : list
        A list of tuples where the first element of each tuple is an object
        suitable for `render()` and the second is the color to apply to that
        object.
    fill : str or None, optional
        A color to use as the background color.  If `None` then no color is
        applied.
    kwargs : **kwargs, optional
        Additional keyword arguments for `render_multiple()`.

    Returns
    -------
    str
        All input layers, features, or geometries rendered, stacked, and styled.
    """

    if fill is None:
        fill_char = ' '
        colormap = {}
    else:
        fill_char = DEFAULT_COLOR_CHAR[fill]
        colormap = {fill_char: fill}

    ftr_char_pairs = []
    for ftrz, color in ftr_color_pairs:
        char = DEFAULT_COLOR_CHAR[color]
        ftr_char_pairs.append((ftrz, char))
        colormap[char] = color

    return style(render_multiple(ftr_char_pairs, fill=fill_char, **kwargs), colormap)


def _bbox_from_arbitrary_iterator(input_iter):

    """
    Compute a bbox from an iterable object containing features, geometries, or
    a feature collection.  Both the bbox and a version of the iterator are
    returned in order to handle iterating over generators twice.  The iterator
    itself is returned if it is not a generator.

    Parameters
    ----------
    iterator : iterable object
        An iterable object returning one GeoJSON feature, or geometry, or
        object supporting `__geo_interface` every iteration.

    Returns
    -------
    tuple
        ((x_min, y_min, x_max, y_max), <iterable>
    """

    if hasattr(input_iter, 'bounds'):
        bbox = input_iter.bounds
        output_iterator = input_iter
    else:
        if isinstance(input_iter, GeneratorType):
            coord_iter, output_iterator = itertools.tee(input_iter)
        else:
            coord_iter = input_iter
            output_iterator = input_iter

        coords = list(itertools.chain(*[asShape(g).bounds for g in _geometry_extractor(coord_iter)]))
        bbox = (min(coords[0::4]), min(coords[1::4]), max(coords[2::4]), max(coords[3::4]))

    return bbox, output_iterator
