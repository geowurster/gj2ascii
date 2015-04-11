#!/usr/bin/env bash

### Simple commands ###

# Render GeoJSON piped from stdin
cat sample-data/polygons.geojson | gj2ascii -

# Render a file with a single layer with a user-specified char and fill
# and a non-default width
gj2ascii sample-data/WV.geojson -w 10 -c \* -f .

# Iterate over every feature in a layer but don't print an attribute table
gj2ascii sample-data/WV.geojson -i

# Same as above but print two attributes
gj2ascii sample-data/WV.geojson -i -p ALAND,AWATER

# Same as above but print all attributes
gj2ascii sample-data/WV.geojson -i -p %all

# Render multiple single-layer files
gj2ascii sample-data/polygons.geojson sample-data/lines.geojson


### Advanced Commands ###

# Same as above but turn off the colors and use user-defined characters
gj2ascii sample-data/polygons.geojson sample-data/lines.geojson -c : -c ^

# Same as above but assign a specific color to each character
gj2ascii sample-data/polygons.geojson sample-data/lines.geojson \
    -c :=yellow \
    -c ^=blue \
    -f @=black

# Render a single multi-layer file
gj2ascii sample-data/multilayer-polygon-line/

# Mix rendering single and multi-layer files
gj2ascii sample-data/multilayer-polygon-line/,polygons sample-data/lines.geojson

# Same as above but clip to the bounds of a different layer
gj2ascii sample-data/multilayer-polygon-line/,polygons sample-data/lines.geojson \
    --bbox sample-data/bbox.geojson
