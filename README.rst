.. code-block:: console

                _ ___                   _ _
       ____ _  (_)__ \ ____ ___________(_|_)
      / __ `/ / /__/ // __ `/ ___/ ___/ / /
     / /_/ / / // __// /_/ (__  ) /__/ / /
     \__, /_/ //____/\__,_/____/\___/_/_/
    /____/___/


.. image:: https://travis-ci.org/geowurster/gj2ascii.svg?branch=master
    :target: https://travis-ci.org/geowurster/gj2ascii


.. image:: https://coveralls.io/repos/geowurster/gj2ascii/badge.svg?branch=master
    :target: https://coveralls.io/r/geowurster/gj2ascii

Render GeoJSON as ASCII with Python and the commandline.


Why?
====

A `tweet <https://twitter.com/vtcraghead/status/575370039701929984>`__ made it seem like an interesting exercise but
the ``gj2ascii`` commandline utility has been very useful for previewing multiple files and the API has proven to be
useful for debugging complex geoprocessing operations.


Examples
========

See the `examples directory <https://github.com/geowurster/gj2ascii/tree/master/examples>`__ for more information and
more complex examples but the following are a good place to get started.  Some of the examples include output that
would be colored if run on the commandline or in Python but RST cannot render the ANSI codes.

Render two layers, one read from stin and one read directly from a file, across 20 pixels while explicitly specifying
a character and color for each layer and background fill, and zooming in on an area of interest.

.. code-block:: console

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



Render individual features across 10 pixels and display the attributes for two
fields, ``COUNTYFP`` and ``NAME``.

.. code-block:: console

    $ gj2ascii sample-data/WV.geojson \
        --iterate \
        --properties COUNTYFP,NAME \
        --width 10

    +----------+---------+
    | COUNTYFP |     001 |
    | NAME     | Barbour |
    +----------+---------+

                + + +
      +   + + + + + + +
      + + + + + + + + +
    + + + + + + + + +
    + + + + + + + + + +
        + + + + + + +
            + + + +
            + + + +

    Press enter for the next geometry or ^C/^D or 'q' to quit...

Recreate the first example with the Python API
----------------------------------------------

There are two ways to recreate the first example with the Python API.  If the user does not care about which characters
are assigned to which color, use this one:

.. code-block:: python

    import fiona as fio
    import gj2ascii
    with fio.open('sample-data/polygons.geojson') as poly, fio.open('sample-data/lines.geojson') as lines, \
            fio.open('sample-data/small-aoi-polygon-line.geojson') as bbox:
        layermap = [
            (poly, 'red'),
            (lines, 'blue')
        ]
        print(gj2ascii.style_multiple(layermap, 20, fill='green', bbox=bbox.bounds))
    0 0 0 0 0 0 1 0 0 0 0 0 0 0 0 0 2 2 2 2
    0 0 0 0 0 1 0 0 0 0 0 0 0 0 0 0 0 2 2 2
    0 0 0 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0 1 1
    0 0 0 0 1 0 0 0 0 0 0 0 0 1 1 1 1 1 0 2
    2 2 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
    2 2 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
    2 1 2 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
    2 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
    1 2 0 0 0 0 0 0 1 0 0 0 0 0 2 0 0 0 0 0
    0 1 0 0 0 0 0 0 1 1 0 0 0 2 2 0 0 0 0 0
    0 0 1 0 0 0 0 0 1 0 1 0 2 2 2 0 0 0 0 0
    0 0 0 1 0 0 0 0 1 0 0 1 2 2 2 0 0 0 0 0
    0 0 0 0 1 0 0 1 0 0 2 2 1 2 2 0 0 0 0 0
    0 0 0 0 0 1 0 1 0 2 2 2 2 1 2 0 0 0 0 0
    0 0 0 0 0 0 1 1 2 2 2 2 2 2 1 0 0 0 0 0


If the user cares about which character is assigned to which layer, use this one:

.. code-block:: python

    import fiona as fio
    import gj2ascii

    with fio.open('sample-data/polygons.geojson') as poly, fio.open('sample-data/lines.geojson') as lines, \
            fio.open('sample-data/small-aoi-polygon-line.geojson') as bbox:

        # Render each layer individually with the same bbox and width
        # The fill will be assigned in the next step but must be a single space here
        rendered_layers = [
            gj2ascii.render(poly, 20, char='^', fill=' ', bbox=bbox.bounds),
            gj2ascii.render(lines, 20, char='-', fill=' ', bbox=bbox.bounds)
        ]

        # Overlay the rendered layers into one stack
        stacked = gj2ascii.stack(rendered_layers, fill='.')

        # Apply the colors and print
        colormap = {
            '^': 'red',
            '-': 'blue',
            '.': 'green'
        }
        print(gj2ascii.style(stacked, colormap))
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

Paginating through features:

.. code-block:: python

    import fiona as fio
    import gj2ascii

    with fio.open('sample-data/WV.geojson') as src:
        for feature in gj2ascii.paginate(src, 10, properties=['COUNTYFP', 'NAME']):
            print(feature)
    +----------+---------+
    | COUNTYFP |     001 |
    | NAME     | Barbour |
    +----------+---------+

                + + +
      +   + + + + + + +
      + + + + + + + + +
    + + + + + + + + +
    + + + + + + + + + +
        + + + + + + +
            + + + +
            + + + +


Installation
============

Via pip:

.. code-block:: console

    $ pip install gj2ascii --upgrade

From master branch:

.. code-block:: console

    $ git clone https://github.com/geowurster/gj2ascii.git
    $ cd gj2ascii
    $ python setup.py install

To enable emoji:

.. code-block:: console

    $ pip install gj2ascii[emoji]


Dependencies
------------

The dependencies are pretty heavy for a utility like this and may require some
extra work to get everything installed.  All dependencies should install on their
own but there are a few potentially problematic packages.  Manually installing
the following might help:

* `Rasterio <https://github.com/mapbox/rasterio#installation>`__
* `Fiona <https://github.com/toblerity/fiona#installation>`__
* `Shapely <https://github.com/toblerity/shapely#installing-shapely>`__

Some Linux distributions require an additional step before installing rasterio:
``apt-get install python-numpy-dev libgdal1h libgdal-dev``.


Developing
==========

.. code-block:: console

    $ git clone https://github.com/geowurster/gj2ascii.git
    $ cd gj2ascii
    $ virtualenv venv
    $ source venv/bin/activate
    $ pip install -r requirements-dev.txt -e .
    $ nosetests --with-coverage


License
=======

See ``LICENSE.txt``.
