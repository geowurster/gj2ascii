#!/usr/bin/env python


"""
Page through multiple features and display an attribute table for each
"""


import fiona as fio
import gj2ascii


print("Render every feature and its attribute table")
with fio.open('sample-data/WV.geojson') as src:
    for feature in gj2ascii.paginate(src, properties=list(src.schema['properties'].keys())):
        print(feature)
