#!/usr/bin/env python


"""
Setup script for gj2ascii
"""


import setuptools


with open('README.rst') as f:
    readme_content = f.read().strip()


with open('requirements.txt') as f:
    install_requires = f.read().strip()


with open('LICENSE.txt') as f:
    license_content = f.read().strip()


version = None
author = None
email = None
source = None
with open('gj2ascii.py') as f:
    for line in f:
        if line.strip().startswith('__version__'):
            version = line.split('=')[1].strip().replace('"', '').replace("'", '')
        elif line.strip().startswith('__author__'):
            author = line.split('=')[1].strip().replace('"', '').replace("'", '')
        elif line.strip().startswith('__email__'):
            email = line.split('=')[1].strip().replace('"', '').replace("'", '')
        elif line.strip().startswith('__source__'):
            source = line.split('=')[1].strip().replace('"', '').replace("'", '')
        elif None not in (version, author, email, source):
            break


setuptools.setup(
    name='gj2ascii',
    author=author,
    author_email=email,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Topic :: Text Processing :: Filters',
        'Topic :: Text Processing :: General',
        'Topic :: Utilities'
    ],
    description="Render GeoJSON as ASCII on the commandline.",
    entry_points="""
        [console_scripts]
        gj2ascii=gj2ascii:main
    """,
    include_package_data=True,
    install_requires=install_requires,
    license=license_content,
    long_description=readme_content,
    py_modules=['gj2ascii'],
    url=source,
    version=version,
    zip_safe=True,
)
