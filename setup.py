#!/usr/bin/env python


"""Setup script for ``gj1ascii``."""


import itertools as it
import os

from setuptools import find_packages
from setuptools import setup


with open('README.rst') as f:
    readme = f.read().strip()


def parse_dunder_line(string):

    """Take a line like:

        "__version__ = '0.0.8'"

    and turn it into a tuple:

        ('__version__', '0.0.8')

    Not very fault tolerant.
    """

    # Split the line and remove outside quotes
    variable, value = (s.strip() for s in string.split('=')[:2])
    value = value[1:-1].strip()
    return variable, value


with open(os.path.join('gj2ascii', '__init__.py')) as f:
    dunders = dict(map(
        parse_dunder_line, filter(lambda l: l.rstrip().startswith('__'), f)))
    version = dunders['__version__']
    author = dunders['__author__']
    email = dunders['__email__']
    source = dunders['__source__']


extras_require = {
    'test': ['pytest>=3', 'pytest-cov', 'coveralls'],
    'emoji': ['emoji>=0.3.4']
}
extras_require['all'] = list(it.chain.from_iterable(extras_require.values()))


setup(
    name='gj2ascii',
    author=author,
    author_email=email,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Intended Audience :: Information Technology',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Multimedia :: Graphics :: Presentation',
        'Topic :: Scientific/Engineering :: GIS',
        'Topic :: Utilities'
    ],
    description="Render geospatial vectors as text.",
    entry_points="""
        [console_scripts]
        gj2ascii=gj2ascii.cli:main
    """,
    include_package_data=True,
    install_requires=[
        'click>=3.0',
        'fiona>=1.2',
        'numpy>=1.8',
        'rasterio>=0.18',
        'shapely'
    ],
    extras_require=extras_require,
    keywords='geojson ascii text emoji gis vector render',
    license="New BSD",
    long_description=readme,
    packages=find_packages(exclude=['tests']),
    url=source,
    version=version,
    zip_safe=True
)
