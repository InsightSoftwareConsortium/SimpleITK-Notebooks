# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import os
# import sys
# sys.path.insert(0, os.path.abspath('.'))

# PreProcessing:
from pathlib import Path
import shutil
print("########################")
print("########################")
print("########################")
print("########################")

ROOT_DIR = Path.cwd().parent.parent
print(ROOT_DIR )

COPYFROM = ROOT_DIR 
COPYTO = ROOT_DIR / "docs" / "source"
print(COPYFROM)
print(COPYTO)
folders = ["Python", "Data", "Utilities"]
for num, folder in enumerate(folders): 
    print("######")
    folder_from = COPYFROM/ folder
    folder_to = COPYTO /folder
    print(f"{folder_from}")
    print(f"{folder_to}")
    shutil.copytree(folder_from, folder_to)
    print("******DONE*******")

# -- Project information -----------------------------------------------------

project = 'SimpleITK-Notebooks'
copyright = 'NumFOCUS'

# The full version, including alpha/beta/rc tags
release = '11/2021'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx_copybutton',
    'nbsphinx'
]
nbsphinx_allow_errors = True
nbsphinx_execute = 'never'

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'furo'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
#html_static_path = ['_static']
