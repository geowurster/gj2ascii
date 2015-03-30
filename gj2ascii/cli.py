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


def _callback_fill_and_value(ctx, param, value):

    """
    Click callback to validate --fill and --value.
    """

    output = OrderedDict()

    if isinstance(value, string_types):
        _value = value,
    else:
        _value = value

    for v_c in _value:

        _split = v_c.split('=')

        if len(_split) is 2:
            char, color = _split
            color = color.lower()
        else:
            char = _split[0]
            color = None

        if char in output:
            raise click.ClickException("specified character `%s' multiple times" % char)
        else:
            output[char] = color

    _cmode = None
    for char, color in output.items():

        if _cmode is None and color in gj2ascii.ANSI_COLOR_MAP.keys():
            _cmode = 'color'
        elif _cmode is None and color is None:
            _cmode = 'char'

        if len(char) is not 1:
            raise click.BadParameter("`%s' is invalid - must be a single character" % char)
        if _cmode is 'char' and color in gj2ascii.ANSI_COLOR_MAP.keys():
            raise click.BadParameter("specified a color - must do `--character char=color` specify for every value")

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
            return [float(i) for i in value.split()]
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
    '-w', '--width', type=click.INT, default=gj2ascii.DEFAULT_WIDTH,
    help="Render geometry across N columns.  Note that a space is inserted "
         "between each column so the actual number of columns is `(width * 2) - 1`"
)
@click.option(
    '-i', '--iterate', is_flag=True,
    help="Iterate over input features and display each individually."
)
@click.option(
    '-f', '--fill', 'fill_map', default=gj2ascii.DEFAULT_FILL, metavar='CHAR', callback=_callback_fill_and_value,
    help="Single character for non-geometry pixels."
)
@click.option(
    '-c', '--character', 'char_map', default='+', metavar='CHAR', multiple=True, callback=_callback_fill_and_value,
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
    
    # ==== Additional argument adjustment and validation ==== #
    num_layers = sum([len(layers) for ds, layers in infile])

    # User didn't specify any characters/colors but the number of input layers exceeds the number of available colors.
    if num_layers > len(gj2ascii.ANSI_COLOR_MAP) and len(char_map) is 0:
        raise click.ClickException("can't auto-generate color ramp - number of input layers exceeds number of colors.  "
                                   "Specify one value per layer with `--value CHARACTER`.")

    # User didn't specify any characters/colors so one is auto-generated
    elif num_layers > 1 and char_map != {gj2ascii.DEFAULT_CHAR: None}:
        char_map = OrderedDict(
            ((gj2ascii.DEFAULT_CHAR_RAMP, gj2ascii.DEFAULT_COLOR_MAP[str(i)]) for i in range(num_layers)))

    # Make sure fill value doesn't clash with char values
    for c in fill_map:  # This should only be one key
        if c in char_map:
            raise click.ClickException("fill character `%s' also specified in values: %s" % str(list(char_map.keys())))

    # Merge the fill map and character map into one single colormap
    colormap = dict(fill_map, **char_map)
    if None in colormap.values() and len([i for i in colormap.keys() if i in gj2ascii.ANSI_COLOR_MAP.keys()]) > 0:
        raise click.ClickException("when explicitly specifying colors a color must be assigned to every character and "
                                   "the fill character.")
    elif None in colormap.values():
        colormap = {}

    # ==== Iterate over all features in the input layer.  Can only process one layer. ==== #
    if iterate:

        if outfile.name != sys.stdout.name:
            no_prompt = True

        if len(infile) > 1 or num_layers > 1 or len(crs_def) > 1 \
                or len(fill_map) > 1 or len(char_map) > 1 or len(all_touched) > 1:
            raise click.ClickException(
                "Can only iterate over 1 layer - all associated arguments can only be specified once")

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
                'fill': list(fill_map.keys())[-1],
                'properties': properties,
                'all_touched': all_touched[-1],
                'bbox': bbox,
                'colormap': colormap
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

        if len(crs_def) is 1:
            crs_def = crs_def * num_layers

        if not bbox:
            coords = []
            for ds, layer_names in infile:
                for layer, crs in zip_longest(layer_names, crs_def):
                    with fio.open(ds, layer=layer, crs=crs) as src:
                        coords += list(src.bounds)
            bbox = (min(coords[0::4]), min(coords[1::4]), max(coords[2::4]), max(coords[3::4]))

        rendered_layers = []
        for ds, layer_names in infile:
            for layer, crs, char, at in zip_longest(layer_names, crs_def, char_map, all_touched):
                with fio.open(ds, layer=layer, crs=crs) as src:
                    rendered_layers.append(
                        gj2ascii.render(src, width=width, fill=' ', all_touched=at, bbox=bbox))
        output = gj2ascii.stack(rendered_layers, fill=list(fill_map.keys())[-1])
        if colormap:
            output = gj2ascii.style(output, colormap=colormap)
        click.echo(output, file=outfile)












    #
    # # ===== Stack multiple layers and render as a single block
    # elif '%all' in layer_name or len(layer_name) > 1:
    #     for arg in (crs_def, fill_map, char_map, all_touched):
    #         if len(arg) not in (1, len(layer_name)):
    #             raise click.ClickException("Stacking %s layers - all associated arguments can be specified "
    #                                        "only once to apply to all layers or once per layer." % len(layer_name))
    #
    #     if '%all' in layer_name:
    #         layer_name = fio.listlayers(infile)
    #
    #     # User didn't specify a bounding box.  Compute the minimum bbox for all layers.
    #     if not bbox:
    #         coords = []
    #         for layer, crs in zip_longest(layer_name, crs_def):
    #             with fio.open(infile, layer=layer, crs=crs) as src:
    #                 coords += list(src.bounds)
    #         bbox = (min(coords[0::4]), min(coords[1::4]), max(coords[2::4]), max(coords[3::4]))
    #
    #     if len(char_map) is 1:
    #         char_map = gj2ascii.DEFAULT_RAMP[:len(layer_name)]
    #
    #     rendered_layers = []
    #     expected_crs = None
    #     for layer, value, crs, at in zip_longest(layer_name, char_map, crs_def, all_touched):
    #         with fio.open(infile, layer=layer, crs=crs) as src:
    #
    #             # Warn user of differing CRS
    #             if expected_crs is None:  # pragma no cover
    #                 expected_crs = src.crs
    #             else:
    #                 if src.crs != expected_crs:  # pragma no cover
    #                     click.echo(
    #                         "WARNING: Layer `%s' has a differing CRS - results may be incorrect" % layer, err=True)
    #
    #             r_kwargs = {
    #                 'width': width,
    #                 'value': value,
    #                 'fill': ' ',
    #                 'all_touched': at,
    #                 'bbox': bbox
    #             }
    #             rendered_layers.append(gj2ascii.render(src, **r_kwargs))
    #     click.echo(gj2ascii.stack(rendered_layers, fill=fill_map), file=outfile)
    #
    # # ===== Simplest case - only rendering a single layer
    # else:
    #
    #     if len(layer_name) > 1 or len(crs_def) > 1 or len(char_map) > 1 or len(all_touched) > 1:
    #         raise click.ClickException(
    #             "Only rendering 1 layer - all associated arguments can only be specified once.")
    #
    #     with fio.open(
    #             infile, layer=layer_name[-1] if layer_name else None, crs=crs_def[-1] if crs_def else None) as src:
    #         kwargs = {
    #             'width': width,
    #             'value': char_map[-1],
    #             'fill': fill_map,
    #             'all_touched': all_touched[-1],
    #             'bbox': src.bounds if not bbox else bbox
    #         }
    #         click.echo(gj2ascii.render(src, **kwargs), file=outfile)
