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

## deleting all files in docs/source, when they should exist
# DOCS_SOURCE_DIR = Path.cwd()  / "source"
# print(DOCS_SOURCE_DIR)

# folders = ["Python", "Data", "Utilities"]
# for folder in folders:
#     print(DOCS_SOURCE_DIR / folder)
#     try:
#         shutil.rmtree(DOCS_SOURCE_DIR/folder)
#     except FileNotFoundError:
#         print(f"Directory {DOCS_SOURCE_DIR/folder} was not yet in docs/source, so not deleted.")

# Copy notebooks to source

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

# delete all notebooks that are not wanted
NEWLOCATION = ROOT_DIR / "docs" / "source"
exclude_notobooks = [
"Python/00_Setup.ipynb",
"Python/01_Image_Basics.ipynb",
"Python/02_Pythonic_Image.ipynb",
"Python/03_Image_Details.ipynb",
"Python/04_Image_Display.ipynb",
"Python/05_Results_Visualization.ipynb",
"Python/10_matplotlibs_imshow.ipynb",
"Python/11_Progress.ipynb",
#"Python/20_Expand_With_Interpolators.ipynb",
#"Python/21_Transforms_and_Resampling.ipynb",
#"Python/22_Transforms.ipynb",
#"Python/300_Segmentation_Overview.ipynb",
#"Python/30_Segmentation_Region_Growing.ipynb",
#"Python/31_Levelset_Segmentation.ipynb",
#"Python/32_Watersheds_Segmentation.ipynb",
#"Python/33_Segmentation_Thresholding_Edge_Detection.ipynb",
#"Python/34_Segmentation_Evaluation.ipynb",
#"Python/35_Segmentation_Shape_Analysis.ipynb",
#"Python/36_Microscopy_Colocalization_Distance_Analysis.ipynb",
#"Python/51_VH_Segmentation1.ipynb",
"Python/55_VH_Resample.ipynb",
#"Python/56_VH_Registration1.ipynb",
#"Python/60_Registration_Introduction.ipynb",
#"Python/61_Registration_Introduction_Continued.ipynb",
#"Python/62_Registration_Tuning.ipynb",
#"Python/63_Registration_Initialization.ipynb",
#"Python/64_Registration_Memory_Time_Tradeoff.ipynb",
#"Python/65_Registration_FFD.ipynb",
"Python/66_Registration_Demons.ipynb",
"Python/67_Registration_Semiautomatic_Homework.ipynb",
"Python/68_Registration_Errors.ipynb",
"Python/69_x-ray-panorama.ipynb",
"Python/70_Data_Augmentation.ipynb",
"Python/71_Trust_But_Verify.ipynb",
]

for nb in exclude_notobooks:
    excluded_notebook = NEWLOCATION/nb
    print(excluded_notebook)
    excluded_notebook.unlink()


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
#nbsphinx_execute = 'never'

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
