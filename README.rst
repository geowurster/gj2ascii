========
gj2ascii
========

Render GeoJSON as ASCII on the commandline.

Inspired by `@vtcraghead <twitter.com/vtcraghead>`__, `@dnomadb <twitter.com/dnomadb>`__, and
`Twitter <https://twitter.com/vtcraghead/status/575370039701929984>`__.  Needs a better name.


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


Caveats
=======

The aspect ration of a character on the commandline is not equal so there is some
vertical distortion.

Relies on [Fiona](http://toblerity.org/fiona/) for reading vector data, so
reading delimited JSON or JSON from a file or ``stdin`` is not yet supported.  It
would be extra slick if this could take the output from ``fio cat``.


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
    $ pip install -e .
