#!/usr/bin/env python


"""
Render multiple overlapping layers and zoom in on an area of interest
"""


import gj2ascii
import fiona as fio


print("Render both layers")
with fio.open('sample-data/polygons.geojson') as poly, \
        fio.open('sample-data/lines.geojson') as lines, \
        fio.open('sample-data/bbox.geojson') as bbox:
    layermap = [
        (poly[0], '0'),
        (lines[0], '1')
    ]
    print(gj2ascii.render_multiple(layermap, 40, fill='.', bbox=bbox.bounds))

print("")

print("Render one feature from each layer")
with fio.open('sample-data/polygons.geojson') as poly, \
        fio.open('sample-data/lines.geojson') as lines, \
        fio.open('sample-data/bbox.geojson') as bbox:
    layermap = [
        (poly[0], '0'),
        (lines[0], '1')
    ]
    print(gj2ascii.render_multiple(layermap, 40, fill='.', bbox=bbox.bounds))

print("")

print("Render one feature and one geometry that are both independent from a Fiona")
print("collection.  In this case the bbox will be computed on the fly")
with fio.open('sample-data/polygons.geojson') as poly, \
        fio.open('sample-data/lines.geojson') as lines:
    feature = poly[0]
    geometry = lines[0]['geometry']

layermap = [
    (feature, '0'),
    (geometry, '1')
]
print(gj2ascii.render_multiple(layermap, 40))
