"""
Commandline interface for gj2ascii

See `gj2ascii --help` for more info.

$ cat sample-data/polygons.geojson | gj2ascii - \
    sample-data/lines.geojson \
    --bbox sample-data/small-aoi-polygon-line.geojson \
    --width 20 \
    --char ^=red \
    --char -=blue \
    --fill .=green
. . . . . . - . . . . . . . . . ^ ^ ^ ^
. . . . . - . . . . . . . . . . . ^ ^ ^
. . . . - . . . . . . . . . . . . . - -
. . . . - . . . . . . . . - - - - - . ^
^ ^ . - . . . . . . . . . . . . . . . .
^ ^ - . . . . . . . . . . . . . . . . .
^ - ^ . . . . . . . . . . . . . . . . .
^ - . . . . . . . . . . . . . . . . . .
- ^ . . . . . . - . . . . . ^ . . . . .
. - . . . . . . - - . . . ^ ^ . . . . .
. . - . . . . . - . - . ^ ^ ^ . . . . .
. . . - . . . . - . . - ^ ^ ^ . . . . .
. . . . - . . - . . ^ ^ - ^ ^ . . . . .
. . . . . - . - . ^ ^ ^ ^ - ^ . . . . .
. . . . . . - - ^ ^ ^ ^ ^ ^ - . . . . .
"""


from collections import OrderedDict
import os
import sys

import gj2ascii
from .pycompat import zip_longest
from .pycompat import string_types

import click
import fiona as fio


def _build_colormap(c_map, f_map):

    """
    Combine a character and fill map into a single colormap
    """

    return {k: v for k, v in c_map + f_map if v is not None}


def _cb_char_and_fill(ctx, param, value):

    """
    Click callback to validate --fill and --char.  --char supports multiple
    syntaxes but they cannot be mixed: +, blue, +=blue.

    This whole thing works but needs to be cleaned up.
    """

    # If the user didn't supply anything then value=None
    if value is None:
        value = ()
    elif isinstance(value, string_types):
        value = value,
    else:
        value = value

    output = []
    for val in value:
        if len(val) is 1:
            output.append((val, None))
        elif '=' in val:
            output.append(val.rsplit('=', 1))
        else:
            try:
                char = gj2ascii.DEFAULT_COLOR_CHAR[val]
            except KeyError:
                raise click.BadParameter(
                    "must be a single character, color, or emoji, not: `{val}'.".format(
                        val=val)
                )
            output.append((char, val))

    return output


def _cb_properties(ctx, param, value):

    """
    Click callback to validate --parameters.
    """

    if value in ('%all', None):
        return value
    else:
        return value.split(',')


def _cb_multiple_default(ctx, param, value):

    """
    Options that can be specified multiple times are an empty tuple if they are
    never specified.  This callback wraps the default value in a tuple if the
    argument is not specified at all.
    """

    if len(value) is 0:
        return param.default,
    else:
        return value


def _cb_bbox(ctx, param, value):

    """
    Validate ``--bbox`` by making sure it doesn't form a 'bow-tie'.
    """

    if value:
        x_min, y_min, x_max, y_max = value
        if (x_min > x_max) or (y_min > y_max):
            raise click.BadParameter(
                'self-intersection: {bbox}'.format(bbox=value))

    return value


def _cb_infile(ctx, param, value):

    """
    Let the user specify a datasource and its layers in a single argument.

    Example usage:

        Render all layers in a datasource
        $ gj2ascii sample-data/multilayer-polygon-line

        Render layer with name 'polygons' in a multilayer datasource
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
        if ds != '-' and (len(layers) is 0 or '%all' in layers):
            layers = fio.listlayers(ds)
        elif ds == '-':
            layers = [None]
        output.append((ds, layers))

    return output


@click.command()
@click.version_option(version=gj2ascii.__version__)
@click.argument('infile', nargs=-1, required=True, callback=_cb_infile)
@click.option(
    '-o', '--outfile', type=click.File(mode='w'), default='-',
    help="Write to an output file instead of stdout."
)
@click.option(
    '-w', '--width', type=click.INT, default=40,
    help="Render geometry across N columns.  A single space is inserted between each column "
         "so the actual number of columns is `width * 2`."
)
@click.option(
    '-i', '--iterate', is_flag=True,
    help="Iterate over input features and display each individually."
)
@click.option(
    '-f', '--fill', 'fill_map', metavar='CHAR', default=gj2ascii.DEFAULT_FILL,
    callback=_cb_char_and_fill,
    help="Single character to use for pixels that are not covered by a geometry."
)
@click.option(
    '-c', '--char', 'char_map', metavar='CHAR', multiple=True, callback=_cb_char_and_fill,
    help="Character to use for pixels that intersect a geometry.  Several syntaxes are "
         "supported: `-c +`, `-c blue`, and `-c +=blue`.  The first will use + and no color, "
         "the second will select a character in the range 0 to 9 and produce blue geometries, "
         "and the last will use + and produce blue geometry."
)
@click.option(
    '--all-touched / --no-all-touched', '-at / -nat', multiple=True, default=False,
    callback=_cb_multiple_default,
    help="Fill all pixels that intersect a geometry instead of those whose center intersects "
         "a geometry."
)
@click.option(
    '--crs', 'crs_def', metavar='DEF', multiple=True, callback=_cb_multiple_default,
    help="Specify input CRS.  No transformations are performed but this will override the "
         "input CRS or assign a new one."
)
@click.option(
    '--no-prompt', is_flag=True,
    help="Print all geometries without pausing in between."
)
@click.option(
    '-p', '--properties', metavar='NAME,NAME,...', callback=_cb_properties,
    help="When iterating over features display the specified fields above each geometry.  Use "
         "`%all` for all."
)
@click.option(
    '--bbox', nargs=4, type=click.FLOAT, metavar="X_MIN Y_MIN X_MAX Y_MAX", callback=_cb_bbox,
    help="Only render data within the bounding box.  If not specified a minimum bounding box "
         "will be computed from all input layers, which can be expensive."
)
@click.option(
    '--no-color', is_flag=True,
    help="Disable colors even if they are specify with `--char`."
)
def main(infile, outfile, width, iterate, fill_map, char_map, all_touched, crs_def, no_prompt,
         properties, bbox, no_color):

    """
    Render spatial vector data on the commandline as ASCII.

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

    fill_char = [c[0] for c in fill_map][-1]
    num_layers = sum([len(layers) for ds, layers in infile])

    # ==== Render individual features ==== #
    if iterate:

        if num_layers > 1:
            raise click.ClickException(
                "Can only iterate over a single layer.  Specify only one infile for "
                "single-layer datasources and `INFILE,LAYERNAME` for multi-layer datasources.")

        if len(infile) > 1 or num_layers > 1 or len(crs_def) > 1 \
                or len(char_map) > 1 or len(all_touched) > 1:
            raise click.ClickException(
                "Can only iterate over 1 layer - all layer-specific arguments can only be "
                "specified once each.")

        # User is writing to an output file.  Don't prompt for next feature every time
        # TODO: Don't just compare to '<stdout>' but sys.stdout.name throws an exception
        if not no_prompt and hasattr(outfile, 'name') and outfile.name != '<stdout>':
            no_prompt = True

        if not char_map:
            char_map = [(gj2ascii.DEFAULT_CHAR, None)]

        # The odd list slicing is due to infile looking something like this:
        # [
        #     ('sample-data/polygons.geojson', ['polygons']),
        #     ('sample-data/multilayer-polygon-line', ['lines', 'polygons'])
        # ]
        if num_layers > 0:
            layer = infile[-1][1][-1]
        else:
            layer = None
        in_ds = infile[-1][0]
        if in_ds == '-' and not no_prompt:

            # This exception blocks a feature - see the content for more info.
            raise click.ClickException(
                "Unfortunately features cannot yet be directly iterated over when reading "
                "from stdin.  The simplest workaround is to use:" + os.linesep * 2 +
                "    $ cat data.geojson | gj2ascii - --iterate --no-prompt | more" + 
                os.linesep * 2 +
                "This issue has been logged: https://github.com/geowurster/gj2ascii/issues/25"
            )
        with fio.open(infile[-1][0], layer=layer, crs=crs_def[-1]) as src:

            if properties == '%all':
                properties = src.schema['properties'].keys()

            # Get the last specified parameter when possible in case there's a bug in the
            # validation above.
            kwargs = {
                'width': width,
                'char': [_c[0] for _c in char_map][-1],
                'fill': fill_char,
                'properties': properties,
                'all_touched': all_touched[-1],
                'bbox': bbox,
                'colormap': _build_colormap(char_map, fill_map)
            }
            if no_color:
                kwargs['colormap'] = None

            for feature in gj2ascii.paginate(src.filter(bbox=bbox), **kwargs):
                click.echo(feature, file=outfile)
                if not no_prompt and click.prompt(
                        "Press enter for next feature or 'q + enter' to exit",
                        default='', show_default=False, err=True) \
                        not in ('', os.linesep):  # pragma no cover
                    raise click.Abort()

    # ==== Render all input layers ==== #
    else:

        # if len(crs_def) not in (1, num_layers) or len(char_map) not in (0, 1, num_layers) \
        #     or len(all_touched) not in (1, num_layers)

        # User didn't specify any characters/colors but the number of input layers exceeds
        # the number of available colors.
        if not char_map:
            if num_layers > len(gj2ascii.ANSI_COLORMAP):
                raise click.ClickException(
                    "can't auto-generate color ramp - number of input layers exceeds number "
                    "of colors.  Specify one `--char` per layer.")
            elif num_layers is 1:
                char_map = [(gj2ascii.DEFAULT_CHAR, None)]
            else:
                char_map = [(str(_i), gj2ascii.DEFAULT_CHAR_COLOR[str(_i)])
                            for _i in range(num_layers)]
        elif len(char_map) is not num_layers:
            raise click.ClickException(
                "Number of `--char` arguments must equal the number of layers being "
                "processed.  Found %s characters and %s layers.  Characters and colors will "
                "be generated if none are supplied." % (len(char_map), num_layers))
        if not char_map:
            char_map = {gj2ascii.DEFAULT_CHAR: None}

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
                char = [_c[0] for _c in char_map][overall_lyr_idx]
                overall_lyr_idx += 1
                with fio.open(ds, layer=layer, crs=crs) as src:
                    rendered_layers.append(
                        # Layers will be stacked, which requires fill to be set to a space
                        gj2ascii.render(
                            src, width=width, fill=' ', char=char, all_touched=at, bbox=bbox))

        stacked = gj2ascii.stack(rendered_layers, fill=fill_char)
        if no_color:
            styled = stacked
        else:
            styled = gj2ascii.style(stacked, stylemap=_build_colormap(char_map, fill_map))
        click.echo(styled, file=outfile)
