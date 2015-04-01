"""
Commandline interface for gj2ascii

    $ gj2ascii ${INFILE} -w 20

      +                       +
      + + +
          +
                              +
                      +
                      + +
                      + + + +
                        + + + +
                          + + +         +
    + + +                   + +       + + +
    + + + +                         + + + +
        +             +               + +
                    + +                 +
                  + + +                 +
                + + + +
                + + + +
                    + +
"""


from collections import OrderedDict
import os
import sys

import gj2ascii
from ._23 import zip_longest
from ._23 import string_types

import click
import fiona as fio


def _callback_char_and_fill(ctx, param, value):

    """
    This whole thing works but needs to be cleaned up.

    Click callback to validate --fill and --char.  --char supports multiple
    syntaxes but they cannot be mixed: +, blue, +=blue.
    """

    invalid_color_error = "color `{color}' is invalid - must be one of the following: {valid_colors}".format(
        valid_colors=', '.join(list(gj2ascii.ANSI_COLORMAP.keys())), color='{color}')

    output = OrderedDict()

    # If the user didn't supply anything then value=None
    if value is None:
        _value = ()
    elif isinstance(value, string_types):
        _value = value,
    else:
        _value = value

    if len(_value) is not len(set(_value)):
        raise click.BadParameter("all characters must be unique.")

    # Make sure all the input values use the same syntax
    def get_cmode(v):
        if '=' in v:
            return 'c=c'
        elif v in gj2ascii.ANSI_COLORMAP.keys():
            return 'color'
        else:
            return 'char'

    cc_pairs = []
    cmode = None
    for char_color in _value:
        if cmode is None:
            cmode = get_cmode(char_color)
        elif cmode != get_cmode(char_color):
            raise click.BadParameter("invalid syntax - all instances of `--char` must use the same syntax.  For "
                                     "example, can't mix `--char +` and `--char blue` and `--char +=blue`.")
        if cmode == 'c=c':
            char, color = char_color.rpartition('=')[::2]
            color = color.lower()
            cc_pairs.append((char, color))
        elif cmode == 'color':
            cc_pairs.append(('lookup', char_color))
        else:
            cc_pairs.append((char_color, None))

    for char, color in cc_pairs:
        if char == 'lookup':
            try:
                char = gj2ascii.DEFAULT_COLOR_CHAR[color]
            except KeyError:  # pragma no cover
                raise click.BadParameter(invalid_color_error.format(color=color))

        if color is not None and color not in gj2ascii.DEFAULT_COLOR_CHAR:  # pragma no cover
            raise click.BadParameter(invalid_color_error.format(color=color))
        elif len(char) is not 1:
            raise click.BadParameter("value must be a single character, color, or character=color.")
        else:
            output[char] = color

    return output


def _callback_properties(ctx, param, value):

    """
    Click callback to validate --parameters.
    """

    if value in ('%all', None):
        return value
    else:
        return value.split(',')


def _callback_multiple_default(ctx, param, value):

    """
    Options that can be specified multiple times are an empty tuple if they are
    never specified.  This callback wraps the default value in a tuple if the
    argument is not specified at all.
    """

    if len(value) is 0:
        return param.default,
    else:
        return value


def _callback_bbox(ctx, param, value):

    """
    Let the user specify a file for the bbox or a string with coordinates.
    """

    if value is None:
        return value
    else:
        try:
            with fio.open(value) as src:
                return src.bounds
        except (OSError, IOError):
            return [float(i) for i in value.split(' ')]
        except Exception:
            raise click.BadParameter('must be a file or "x_min y_min x_max y_max"')


def _callback_infile(ctx, param, value):

    """
    Let the user specify a datasource and its layers in a single argument.

    Example usage:

        # Render all layers in a datasource
        $ gj2ascii sample-data/multilayer-polygon-line

        # Render layer with name 'polygons' in a multilayer datasource
        $ gj2ascii sample-data/multilayer-polygon-line,polygons

        # Render two layers in a specific order in a multilayer datasource
        $ gj2ascii sample-data/multilayer-polygon-line,lines,polygons

        # Render layers from multiple files
        $ gj2ascii sample-data/polygons.geojson sample-data/multilayer-polygon-line,lines

    Example output:

        [('sample-data/multilayer-polygon-line', ['polygons', 'lines'])]

        [('sample-data/multilayer-polygon-line', ['polygons'])]

        [('sample-data/multilayer-polygon-line', ['lines', 'polygons'])]

        [
            ('sample-data/polygons.geojson', ['polygons']),
            ('sample-data/multilayer-polygon-line', ['lines'])
        ]

    Returns
    -------
    list
        A list of tuples where the first element of each tuple is the datasource
        and the second is a list of layers to render.
    """

    output = []
    for ds_layers in value:
        _split = ds_layers.split(',')
        ds = _split[0]
        layers = _split[1:]
        if len(layers) is 0 or '%all' in layers:
            layers = fio.listlayers(ds)
        output.append((ds, layers))

    return output


@click.command()
@click.version_option(version=gj2ascii.__version__)
@click.argument('infile', nargs=-1, required=True, callback=_callback_infile)
@click.option(
    '-o', '--outfile', type=click.File(mode='w'), default='-',
    help="Write to an output file instead of stdout."
)
@click.option(
    '-w', '--width', type=click.INT, default=40,
    help="Render geometry across N columns.  Note that an additional character "
         "is inserted between each column so the actual number of columns is "
         "`(width * 2) - 1`.  By default everything is rendered across the entire "
         "terminal window."
)
@click.option(
    '-i', '--iterate', is_flag=True,
    help="Iterate over input features and display each individually."
)
@click.option(
    '-f', '--fill', 'fill_map', metavar='CHAR', default=gj2ascii.DEFAULT_FILL, callback=_callback_char_and_fill,
    help="Single character for non-geometry pixels."
)
@click.option(
    '-c', '--char', 'char_map', metavar='CHAR', multiple=True, callback=_callback_char_and_fill,
    help="Single character for geometry pixels."
)
@click.option(
    '--all-touched / --no-all-touched', '-at / -nat', multiple=True, default=False, callback=_callback_multiple_default,
    help="Fill all pixels that intersect a geometry instead of those whose center "
         "intersects a geometry."
)
@click.option(
    '--crs', 'crs_def', metavar='DEF', multiple=True, callback=_callback_multiple_default,
    help="Specify input CRS.  No transformations are performed but this will "
         "override the input CRS or assign a new one."
)
@click.option(
    '--no-prompt', is_flag=True,
    help="Print all geometries without pausing in between."
)
@click.option(
    '-p', '--properties', metavar='NAME,NAME,...', callback=_callback_properties,
    help="When iterating over features display the specified properties above "
         "each geometry.  Use `%all` for all."
)
@click.option(
    '--bbox', metavar="FILE or COORDS", callback=_callback_bbox,
    help="Render data within bounding box.  Can be a path to a file or coords "
         "as 'x_min y_min x_max y_max'.  If iterating through all features only "
         "those intersecting the bbox will be rendered.  If processing a single "
         "layer the default is to use the layer extent but if processing "
         "multiple layers the minimum bounding box containing all layers is "
         "computed."
)
def main(infile, outfile, width, iterate, fill_map, char_map, all_touched, crs_def, no_prompt, properties, bbox):

    """
    Render GeoJSON on the commandline as ASCII.

    \b
    Examples:
    \b
        Render the entire layer in a block 20 pixels wide:
    \b
            $ gj2ascii ${INFILE} --width 20
    \b
        Read from stdin and fill all pixels that intersect a geometry:
    \b
            $ cat ${INFILE} | gj2ascii - \\
                --width 15 \\
                --all-touched
    \b
        Render individual features across 10 pixels and display the attributes
        for two fields:
    \b
            $ gj2ascii ${INFILE} \\
                --properties ${PROP1},${PROP2}  \\
                --width 10 \\
                --iterate
    """

    fill_char = list(fill_map.keys())[-1]
    num_layers = sum([len(layers) for ds, layers in infile])

    # ==== Render individual features ==== #
    if iterate:

        if num_layers > 1:
            raise click.ClickException("Can only iterate over a single layer.  Specify only one infile for "
                                       "single-layer datasources and `INFILE,LAYERNAME` for multi-layer datasources.")

        if len(infile) > 1 or num_layers > 1 or len(crs_def) > 1 or len(char_map) > 1 or len(all_touched) > 1:
            raise click.ClickException(
                "Can only iterate over 1 layer - all layer-specific arguments can only be specified once each.")

        if not char_map:
            char_map = {gj2ascii.DEFAULT_CHAR: None}
        if fill_char in char_map:
            raise click.BadParameter("fill value `%s' also specified as a character.  If `--fill color` was used the "
                                     "character selected will be an integer between >= 0 and <= 6, which may be "
                                     "what triggered this error if that integer was also specified with `--char`."
                                     % fill_char)

        # User is writing to an output file.  Don't prompt for next feature every time
        if not no_prompt and hasattr(outfile, 'name') and outfile.name != '<stdout>':
            no_prompt = True

        # The odd list slicing is due to infile looking something like this:
        # [
        #     ('sample-data/polygons.geojson', ['polygons']),
        #     ('sample-data/multilayer-polygon-line', ['lines', 'polygons'])
        # ]
        with fio.open(infile[-1][0], layer=infile[-1][1][-1], crs=crs_def[-1]) as src:

            if properties == '%all':
                properties = src.schema['properties'].keys()

            # Get the last specified parameter when possible in case there's a bug in the validation above.
            kwargs = {
                'width': width,
                'char': list(char_map.keys())[-1],
                'fill': fill_char,
                'properties': properties,
                'all_touched': all_touched[-1],
                'bbox': bbox,
                'colormap': {k: v for k, v in dict(char_map, **fill_map).items() if v is not None}
            }
            try:
                for feature in gj2ascii.paginate(src.filter(bbox=bbox), **kwargs):
                    click.echo(feature, file=outfile)
                    if not no_prompt and click.prompt(
                            "Press enter for next feature or 'q + enter' to exit",
                            default='', show_default=False) not in ('', os.linesep):  # pragma no cover
                        raise click.Abort()

            except Exception as e:
                if isinstance(e, click.Abort):  # pragma no cover
                    raise e
                else:
                    raise click.ClickException(repr(e))

    # ==== Render all input layers ==== #
    else:

        # if len(crs_def) not in (1, num_layers) or len(char_map) not in (0, 1, num_layers) \
        #     or len(all_touched) not in (1, num_layers)

        # User didn't specify any characters/colors but the number of input layers exceeds the number
        # of available colors.
        if not char_map:
            if num_layers > len(gj2ascii.ANSI_COLORMAP):
                raise click.ClickException("can't auto-generate color ramp - number of input layers exceeds number of "
                                           "colors.  Specify one `--char` per layer.")
            elif num_layers is 1:
                char_map = {gj2ascii.DEFAULT_CHAR: None}
            else:
                char_map = OrderedDict(((str(_i), gj2ascii.DEFAULT_CHAR_COLOR[str(_i)]) for _i in range(num_layers)))
        elif len(char_map) is not num_layers:
            raise click.ClickException("Number of `--char` arguments must equal the number of layers being processed.  "
                                       "Found %s characters and %s layers.  Characters and colors will be generated if "
                                       "none are supplied." % (len(char_map), num_layers))

        if fill_char in char_map:
            raise click.BadParameter("fill value `%s' also specified as a character.  If `--fill color` was used the "
                                     "character selected will be an integer between >= 0 and <= 6, which may be "
                                     "what triggered this error if that integer was also specified with `--char`."
                                     % fill_char)

        # User didn't specify a bounding box.  Compute the minimum bbox for all layers.
        if not bbox:
            coords = []
            for ds, layer_names in infile:
                for layer, crs in zip_longest(layer_names, crs_def):
                    with fio.open(ds, layer=layer, crs=crs) as src:
                        coords += list(src.bounds)
            bbox = (min(coords[0::4]), min(coords[1::4]), max(coords[2::4]), max(coords[3::4]))

        # Render everything
        rendered_layers = []
        overall_lyr_idx = 0
        for ds, layer_names in infile:
            for layer, crs, at in zip_longest(layer_names, crs_def, all_touched):
                char = list(char_map.keys())[overall_lyr_idx]
                overall_lyr_idx += 1
                with fio.open(ds, layer=layer, crs=crs) as src:
                    rendered_layers.append(
                        # Layers will be stacked, which requires fill to be set to a space
                        gj2ascii.render(src, width=width, fill=' ', char=char, all_touched=at, bbox=bbox))

        stacked = gj2ascii.stack(rendered_layers, fill=fill_char)
        styled = gj2ascii.style(
            stacked, colormap={k: v for k, v in dict(char_map, **fill_map).items() if v is not None})
        click.echo(styled, file=outfile)
