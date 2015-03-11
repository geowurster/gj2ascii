========
gj2ascii
========

Render GeoJSON as ASCII on the commandline.

.. image:: https://travis-ci.org/geowurster/gj2ascii.svg?branch=master
    :target: https://travis-ci.org/geowurster/gj2ascii

.. image:: https://coveralls.io/repos/geowurster/gj2ascii/badge.svg?branch=master
    :target: https://coveralls.io/r/geowurster/gj2ascii



Inspired by @wboykinm, @dnomadb, and `Twitter <https://twitter.com/vtcraghead/status/575370039701929984>`__.  Needs a better name.


.. image:: https://raw.githubusercontent.com/geowurster/gj2ascii/master/docs/WV.png
   :target: https://github.com/geowurster/gj2ascii


Examples
========

By default every geometry is rendered individually and the user paginates through
them by pressing return:

.. image:: https://raw.githubusercontent.com/geowurster/gj2ascii/master/docs/paginate.png
   :target: https://github.com/geowurster/gj2ascii

Use the ``--all`` flag to render the entire layer:

.. image:: https://raw.githubusercontent.com/geowurster/gj2ascii/master/docs/polygons.png
   :target: https://github.com/geowurster/gj2ascii


Installing
==========

Via pip:

.. code-block:: console

    pip install gj2ascii


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
