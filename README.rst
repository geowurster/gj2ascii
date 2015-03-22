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

Render GeoJSON on the commandline.  Inspired by `@wboykinm <https://github.com/wboykinm/>`__, `@dnomadb <https://github.com/dnomadb/>`__, and a `tweet <https://twitter.com/vtcraghead/status/575370039701929984>`__.


Examples
========

Get help:

.. code-block:: console

    $ gj2ascii --help


Render the entire layer in a block 20 pixels wide:

.. code-block:: console

    $ gj2ascii sample-data/polygons.geojson --width 20

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

Read from stdin and render all pixels any geometry touches across 15 pixels:

.. code-block:: console

    $ cat sample-data/polygons.geojson | gj2ascii - --width 15 --all-touched

    + + + +           + +
    + + + +           + +
        + +           + +
                + + +
                + + + +
                  + + + +     +
    + +           + + + +   + + +
    + + +           + + +   + + +
    + + +       + +         + + +
              + + +         + + +
            + + + +           + +
            + + + +
              + + +

Render individual features across 10 pixels and display the attributes for two
fields, ``COUNTYFP`` and ``NAME``.

.. code-block:: console

    $ gj2ascii sample-data/WV.geojson --iterate --properties COUNTYFP,NAME --width 10

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

    +----------+---------+
    | COUNTYFP |     013 |
    | NAME     | Calhoun |
    +----------+---------+

            + +
          + + + + +
        + + + + + + +
    + + + + + + + + +
    + + + + + + + + +
      + + + + + + + +
      + + + + + + + +
        + + + + + + +
        + + + + + +
          + + + + +
            + + + + + +
            + + + + + +
            + + + + +
            + + + +

    Press enter for the next geometry or ^C/^D or 'q' to quit...


Installation
============

Via pip:

.. code-block:: console

    $ pip install gj2ascii

From master branch:

.. code-block:: console

    $ git clone https://github.com/geowurster/gj2ascii.git
    $ cd gj2ascii
    $ python setup.py install

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
``apt-get install python-numpy-dev``


API
===

Read data with `Fiona <https://github.com/toblerity/fiona>`__ but when possible
be sure to populate `x_min`, `y_min`, `x_max`, and `y_max` to avoid a potentially
expensive computation and large in-memory object:

.. code-block:: python

    import fiona
    import gj2ascii
    with fiona.open('sample-data/polygons.geojson') as src:
        kwargs = dict(zip(('x_min', 'y_min', 'x_max', 'y_max'), src.bounds))
        print(gj2ascii.render(src, width=20, **kwargs))
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

Render an entire layer:

.. code-block:: python

    with open('sample-data/lines.geojson') as f:
        features = json.load(f)
        ascii = gj2ascii.render(features['features'], 20)
    print(ascii)
    + + + + + + + + +           +
      +                         +
        +                         +
          +                       +
            +                       +
              +                     +
            +                         +
            +                         +
          +         + + + + + + +     +
        +                               +
      +                                 +
      +                                   +
    +         +                           +
      +       + +
        +     +   +
          + +       +





Render a single feature:

.. code-block:: python

    import json
    import gj2ascii
    with open('sample-data/lines.geojson') as f:
        features = json.load(f)
        ascii = gj2ascii.render(next(features['features']), 15)
    print(ascii)
                  + + + + + + +
    + + + + + + +
    +
      + +
          +
            +
              + +
                  +
                    +
                  +
                +
                +
              +
            +
          +
        +
        +
      +
    +               +
      +             + +
        +           +   +
          +         +   +
            +     +       +
              +   +         +
                + +           +
                  +           +


Get the properties as a formatted table:

.. code-block:: python

    import json
    import gj2json
    with open('sample-data/WV.geojson') as f:
        features = json.load(f)
        table = gj2ascii.dict_table(features['features'][0]['properties'])
    print(table)
    +----------+----------------+
    | INTPTLAT |    +39.1397248 |
    | NAME     |        Barbour |
    | ALAND    |      883338808 |
    | CLASSFP  |             H1 |
    | FUNCSTAT |              A |
    | INTPTLON |   -079.9969466 |
    | LSAD     |             06 |
    | METDIVFP |           None |
    | GEOID    |          54001 |
    | AWATER   |        4639183 |
    | COUNTYFP |            001 |
    | CSAFP    |           None |
    | CBSAFP   |           None |
    | MTFCC    |          G4020 |
    | NAMELSAD | Barbour County |
    | STATEFP  |             54 |
    | COUNTYNS |       01696996 |
    +----------+----------------+


Developing
==========

.. code-block:: console

    $ git clone https://github.com/geowurster/gj2ascii.git
    $ cd gj2ascii
    $ virtualenv venv
    $ source venv/bin/activate
    $ pip install -r requirements-dev.txt
    $ pip install -e .
    $ nosetests --with-coverage


License
=======

See ``LICENSE.txt``.
