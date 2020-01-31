# SimpleITK R Notebooks

## Setting Up an R Environment with Dependencies

1. Install [R](https://www.r-project.org/) on your machine.
2. [Install](http://jupyter.readthedocs.org/en/latest/install.html) the Jupyter environment.
3. [Install](https://github.com/IRkernel/IRkernel) the R kernel for Jupyter.
4. Install the following R packages, at the R prompt: install.packages(c("rPython", "scatterplot3d", "tidyr", "ggplot2", "xtable", "purrr")).


### Install SimpleITK

A devtools based installer is [available on github](https://github.com/SimpleITK/SimpleITKRInstaller). It requires that you have the [CMake tool](https://cmake.org/) and the git version control system installed on your machine.

The manual approach to compiling and installing SimpleITK with the R wrapping turned on is described [here](https://simpleitk.readthedocs.io/en/master/Documentation/docs/source/building.html).


### Downloading Data

The data can be automatically downloaded to the "Data" directory when you execute the notebooks.

Alternatively, to download all the data before hand:

    cd SimpleITK-Notebooks
    ./downloaddata.py Data/ Data/manifest.json

### Working offline

In some situations, such as a tutorial session, you may not have internet access. This requires that you:

1. Download the data in advance - see above.

# View Static Converted Pages

Static views of all pages are available on the [html site of this repository](https://insightsoftwareconsortium.github.io/SimpleITK-Notebooks/).
