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


import os

import gj2ascii
from gj2ascii._core import zip_longest

import click
import fiona as fio


def _callback_fill_and_value(ctx, param, value):

    """
    Click callback to validate --fill and --value.
    """

    for v in value:
        if v is not None and len(v) is not 1:
            raise click.BadParameter('must be a single character')

    return value


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


@click.command()
@click.version_option(version=gj2ascii.__version__)
@click.argument('infile')
@click.argument('outfile', type=click.File(mode='w'), default='-')
@click.option(
    '-l', '--layer', 'layer_name', metavar='NAME', multiple=True, callback=_callback_multiple_default,
    help="Specify input layer for multi-layer datasources."
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
    '-f', '--fill', 'fill_char', default=' ', metavar='CHAR',
    help="Single character for non-geometry pixels."
)
@click.option(
    '-v', '--value', 'value_char', default='+', metavar='CHAR', multiple=True, callback=_callback_fill_and_value,
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
    '--bbox', nargs=4, metavar="X_MIN Y_MIN X_MAX Y_MAX", type=click.FLOAT,
    help="Render data within bounding box.  If iterating through all features "
         "only those intersecting the bbox will be rendered.  If processing a "
         "single layer the default is to use the layer extent but if processing "
         "multiple layers the minimum bounding box containing all layers is "
         "computed."
)
def main(infile, outfile, width, layer_name, iterate, fill_char, value_char, all_touched, crs_def, no_prompt,
         properties, bbox):

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

    # Iterate over every feature in a single input layer
    if iterate:

        if len(layer_name) > 1 or len(crs_def) > 1 or len(fill_char) > 1 or len(value_char) > 1 or len(all_touched) > 1:
            raise click.ClickException(
                "Can only iterate over 1 layer - all associated arguments can only be specified once")

        with fio.open(infile, layer=layer_name[-1], crs=crs_def[-1]) as src:
            kwargs = {
                'width': width,
                'value': value_char,
                'fill': fill_char,
                'properties': properties,
                'all_touched': all_touched,
                'bbox': bbox
            }
            for feature in gj2ascii.paginate(src.filter(bbox=bbox), **kwargs):
                outfile.write(feature)
                if not no_prompt and click.prompt("Press enter for next feature or 'q + enter' to exit",
                                                  default='', show_default=False) not in ('', os.linesep):
                    raise click.Abort()

    # Stack multiple layers and render as a single block
    elif '%all' in layer_name or len(layer_name) > 1:
        for arg in (crs_def, fill_char, value_char, all_touched):
            if len(arg) not in (1, len(layer_name)):
                raise click.ClickException("Stacking %s layers - all associated arguments can be specified "
                                           "only once to apply to all layers or once per layer." % len(layer_name))

        if '%all' in layer_name:
            layer_name = fio.listlayers(infile)

        # User didn't specify a bounding box.  Compute the minimum bbox for all layers.
        if not bbox:
            coords = []
            for layer, crs in zip_longest(layer_name, crs_def):
                with fio.open(infile, layer=layer, crs=crs) as src:
                    coords += list(src.bounds)
            bbox = (min(coords[0::4]), min(coords[1::4]), max(coords[2::4]), max(coords[3::4]))

        if len(value_char) is 1:
            value_char = gj2ascii.DEFAULT_RAMP[:len(layer_name)]

        rendered_layers = []
        for layer, value, crs, at in zip_longest(layer_name, value_char, crs_def, all_touched):
            with fio.open(infile, layer=layer, crs=crs) as src:
                r_kwargs = {
                    'width': width,
                    'value': value,
                    'fill': ' ',
                    'all_touched': at,
                    'bbox': bbox
                }
                rendered_layers.append(gj2ascii.render(src, **r_kwargs))
        outfile.write(gj2ascii.stack(rendered_layers, fill=fill_char))

    # Simplest case - only rendering a single layer
    else:

        if len(layer_name) > 1 or len(crs_def) > 1 or len(fill_char) > 1 or len(value_char) > 1 or len(all_touched) > 1:
            raise click.ClickException(
                "Only rendering 1 layer - all associated arguments can only be specified once.")

        with fio.open(infile, layer=layer_name[-1] if layer_name else None, crs=crs_def[-1] if crs_def else None) as src:
            kwargs = {
                'width': width,
                'value': value_char[-1],
                'fill': fill_char[-1],
                'all_touched': all_touched[-1],
                'bbox': src.bounds if not bbox else bbox
            }
            outfile.write(gj2ascii.render(src, **kwargs))
