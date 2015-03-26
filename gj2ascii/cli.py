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


import itertools
import os
import sys

from . import __version__
from ._core import *
from ._core import zip_longest

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

    output = []
    for properties in value:
        if properties in ('%all', None):
            output.append(properties)
        else:
            output.append(properties.split(','))

    return output


@click.command()
@click.version_option(version=__version__)
@click.argument('infile')
@click.argument('outfile', type=click.File(mode='w'), default='-')
@click.option(
    '-l', '--layer', 'layer_name', metavar='NAME', multiple=True,
    help="Specify input layer for multi-layer datasources."
)
@click.option(
    '-w', '--width', type=click.INT, default=DEFAULT_WIDTH,
    help="Render geometry across N columns.  Note that a space is inserted "
         "between each column so the actual number of columns is `(width * 2) - 1`"
)
@click.option(
    '-i', '--iterate', is_flag=True,
    help="Iterate over input features and display each individually."
)
@click.option(
    '-f', '--fill', 'fill_char', default=' ', metavar='CHAR', multiple=True, callback=_callback_fill_and_value,
    help="Single character for non-geometry pixels."
)
@click.option(
    '-v', '--value', 'value_char', default='+', metavar='CHAR', multiple=True, callback=_callback_fill_and_value,
    help="Single character for geometry pixels."
)
@click.option(
    '-at', '--all-touched', is_flag=True,
    help="Fill all pixels that intersect a geometry instead of those whose center "
         "intersects a geometry."
)
@click.option(
    '--crs', 'crs_def', metavar='DEF', multiple=True,
    help="Specify input CRS."
)
@click.option(
    '--no-prompt', is_flag=True,
    help="Print all geometries without pausing in between."
)
@click.option(
    '-p', '--properties', metavar='NAME,NAME,...', multiple=True, callback=_callback_properties,
    help="When iterating over features display the specified properties above "
         "each geometry.  Use `%all` for all."
)
def main(infile, outfile, width, layer_name, iterate, fill_char, value_char, all_touched, crs_def, no_prompt, properties):

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

    if iterate:

        # When processing multiple layers let the user specify a few flags like --crs and --properties
        # once per --layer or only once to apply to all layers.  The user cannot do something like specify
        # --crs twice but --layer four times.
        # TODO: A click callback can replace this if it has access to all parsed values
        if len(crs_def) is not 1 and len(layer_name) is not len(crs_def):
            raise click.Abort("Specify CRS once to apply to all input layers or once per layer.")
        if len(properties) is not 1 and len(properties) is not len(layer_name):
            raise click.Abort("Specify properties once to apply to all input layers or once per layer.")
        if len(value_char) is not 1 and len(value_char) is not len(layer_name):
            raise click.Abort("Specify value once to apply to all input layers or once per layer.")
        if len(fill_char) is not 1 and len(fill_char) is not len(fill_char):
            raise click.Abort("Specify fill once to apply to all input layers or once per layer.")

        if len(layer_name) is 0:
            layer_name = fio.listlayers(infile)

        for layer, crs, props, fill, value in zip_longest(layer_name, crs_def, properties, fill_char, value_char):
            with fio.open(infile, layer=layer, crs=crs) as src:
                kwargs = {
                    'width': width,
                    'value': value,
                    'fill': fill,
                    'properties': src.schema['properties'] if props == '%all' else props,
                    'all_touched': all_touched
                }
                for feature in paginate(src, **kwargs):

                    outfile.write(feature)

                    if not no_prompt and click.prompt("Press enter for next feature or 'q + enter' to exit",
                                                      default='', show_default=False) not in ('', os.linesep):
                        raise click.Abort()
    else:
        with fio.open(infile, layer=layer_name[0], crs=crs_def) as src:
            kwargs = dict(zip(('x_min', 'y_min', 'x_max', 'y_max'), src.bounds))
            outfile.write(render(src, **kwargs))

    #
    #     with fio.open(infile, layer=layer_name, crs=crs) as src:
    #
    #         if iterate:
    #
    #             if properties == '%all':
    #                 properties = src.schema['properties'].keys()
    #             elif properties is not None:
    #                 for prop in properties:
    #                     if prop not in src.schema['properties']:
    #                         raise ValueError("Property '%s' not in source properties: `%s'"
    #                                          % (prop, ', '.join(src.schema['properties'])))
    #
    #             for feature in paginate(
    #                     src, width=width, fill=fill, value=value, properties=properties, all_touched=all_touched):
    #
    #                 outfile.write(feature)
    #
    #                 if not no_prompt and click.prompt(
    #                         "Press enter for next feature or 'q + enter' to exit", default='', show_default=False) != '':
    #
    #                     raise click.Abort("User stopped feature iteration.")
    #
    #         else:
    #             kwargs = dict(zip(('x_min', 'y_min', 'x_max', 'y_max'), src.bounds))
    #             kwargs.update(all_touched=all_touched)
    #             outfile.write(render(src, width=width, fill=fill, value=value, **kwargs))
    #
    #     sys.exit(0)
    #
    # except Exception as e:
    #     click.echo("ERROR: Encountered an exception - %s" % repr(e), err=True)
    #     sys.exit(1)
