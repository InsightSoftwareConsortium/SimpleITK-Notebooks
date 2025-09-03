# SimpleITK Notebooks

![GitHub Actions Notebook Testing](https://github.com/InsightSoftwareConsortium/SimpleITK-Notebooks/actions/workflows/main.yml/badge.svg
)&nbsp;&nbsp;[![CircleCI Notebook Testing](https://dl.circleci.com/status-badge/img/gh/InsightSoftwareConsortium/SimpleITK-Notebooks/tree/main.svg?style=shield)](https://dl.circleci.com/status-badge/redirect/gh/InsightSoftwareConsortium/SimpleITK-Notebooks/tree/main)
&nbsp;&nbsp;[![http://insightsoftwareconsortium.github.io/SimpleITK-Notebooks/](https://img.shields.io/website-up-down-green-red/http/shields.io.svg)](http://insightsoftwareconsortium.github.io/SimpleITK-Notebooks/)
&nbsp;&nbsp;[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)


[SimpleITK](https://itk.org/Wiki/SimpleITK) is an abstraction layer and wrapper around the Insight Segmentation and Registration Toolkit [(ITK)](http://www.itk.org). It is available in the following programming languages: C++, Python, R, Java, C#, Lua, Tcl and Ruby.

This repository contains a collection of Jupyter Notebooks illustrating the use of SimpleITK for educational and research activities. The notebooks demonstrate the use of SimpleITK for interactive image analysis using the Python and R programming languages.

The repository and its contents can be used for:
1. Learning SimpleITK.
2. As a basis for your teaching activities.
3. As a basis for your research activities.

For the latter two use cases you can take advantage of the the repository's infrastructure which supports remote data downloads and notebook testing. These readily facilitate collaborative research.

The animation below is a visualization of a rigid CT/MR registration process
created with SimpleITK and Python (the [script](Utilities/intro_animation.py) used to generate the frames for the animated gif is found in the repository's Utilities directory).

![](registration_visualization.gif)

# Getting Started

Note that currently SimpleITK with R is only available on Linux and Mac.

1. Language specific details for installing the notebooks is given in the README files in the respective directories ([Python](Python/README.md), [R](R/README.md)). For general information about installing SimpleITK please see the [SimpleITK read-the-docs](https://simpleitk.readthedocs.io/en/master/) pages.

2. The [SimpleITK API documentation](https://simpleitk.org/doxygen/latest/html/index.html) is based on the C++ implementation which is readily mapped to your language of choice.

3. Learn the general concepts underlying the implementations of segmentation and registration by reading the ([ITK book](https://itk.org/ItkSoftwareGuide)). The relevant portion is "Book 2: Design and Functionality". The ITK API is significantly different from the SimpleITK one, but the general concepts are the same (e.g. combination of optimizer and similarity metric for registration).     

4. General notebook setup. By default the contents of the Jupyter notebooks do not occupy the full browser window width. To take advantage of the full window width you can either configure each notebook independently by adding the following into a code cell:
```
from IPython.core.display import display, HTML
display(HTML("<style>.container { width:100% !important; }</style>"))
```
Or apply this configuration to all notebooks by adding the following to
the custom.css jupyter configuration file:
```
.container { width:100% !important; }
```
On OSX/Linux this file is found in `~/.jupyter/custom/custom.css` on windows it is
found in `C:\Users\[your_user_name]\.jupyter\custom\custom.css`.

# Kicking the Tires

Before you clone the repository to your computer you may want to try it out, kick the tires so to speak.

Thanks to the awesome people from the [Binder Project](https://github.com/jupyterhub/binderhub)
you can try out the Python notebooks without installing a thing.

Some caveats:

1. This is a free public service with limited resources, so may not always be available.
2. Some of our notebooks require significant computational
   resources which may not be available.
3. All cells that use the sitk.Show() command will generate an exception because they
   require a Fiji installation. Either ignore this or modify the code
   for the session.

After you launch binder, go to the Python directory and select the notebook of interest:

[![Binder](https://mybinder.org/badge.svg)](https://mybinder.org/v2/gh/InsightSoftwareConsortium/SimpleITK-Notebooks/master)

# Contributions from the Community

We encourage contributions from the community!!!

1. Ask questions on the [ITK discourse](https://discourse.itk.org/).
2. Report issues you encounter (compatibility/bugs) using the
   [GitHub issue reporting system](https://guides.github.com/features/issues/).
2. Contribute code ([instructions](CONTRIBUTING.md)):
   1. bug fixes.
   2. improved versions of existing notebooks, both text and code.
   3. new notebooks.

# How to Cite

If you find these notebooks or the notebook testing infrastructure useful in your research, support our efforts by citing it as:

Z. Yaniv, B. C. Lowekamp, H. J. Johnson, R. Beare, "SimpleITK Image-Analysis Notebooks: a Collaborative Environment for Education and Reproducible Research", J Digit Imaging., https://doi.org/10.1007/s10278-017-0037-8, 31(3): 290-303, 2018.
