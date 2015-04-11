#!/usr/bin/env python


"""
Rendering an entire layer and a single user-defined GeoJSON geometry object
with the most common parameters.
"""


import os

import gj2ascii
import fiona as fio


diamond = {
    'type': 'LineString',
    'coordinates': [[-10, 0], [0, 10], [10, 0], [0, -10], [-10, 0]]
}

print("Render a single independent geometry")
print(gj2ascii.render(diamond, 20, char='*', fill='.'))

print("")

print("Render an entire layer")
with fio.open('sample-data/WV.geojson') as src:
    print(gj2ascii.render(src, width=20, char='*', fill='.'))
