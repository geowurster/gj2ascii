#!/usr/bin/env python


"""
Render data with colors
"""


import fiona as fio
import gj2ascii


print("Render a single layer with colors")
with fio.open('sample-data/polygons.geojson') as src:
    rendered = gj2ascii.render(src, 40, char='+')
    print(gj2ascii.style(rendered, colormap={'+': 'red'}))

print("")

print("Render multiple overlapping layers , apply colors, and zoom in on a bbox")
with fio.open('sample-data/polygons.geojson') as poly, \
        fio.open('sample-data/lines.geojson') as lines, \
        fio.open('sample-data/bbox.geojson') as bbox:
    layermap = [
        (poly, 'red'),
        (lines, 'blue')
    ]
    print(gj2ascii.style_multiple(layermap, 40, fill='yellow', bbox=bbox.bounds))
