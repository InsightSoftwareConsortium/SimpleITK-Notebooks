# SimpleITK Python Notebooks

As of this writing, SimpleITK version >=1.2 or newer is required to run these notebooks. This version is available from [PyPi](https://pypi.python.org/pypi/SimpleITK) and [Anaconda Cloud](https://anaconda.org/simpleitk/simpleitk).

## Setting Up a Python Environment

We recommend setting up a separate Python virtual environment to run through these notebooks as a tutorial.

## Anaconda
With [Anaconda](https://www.continuum.io/) you can set up a virtual environment, named sitkpy, and install all dependencies including SimpleITK using a single command:

    conda env create -f environment.yml

### Run the notebooks

To launch:

    conda activate sitkpy
    jupyter notebook

To deactivate the conda environment:

    conda deactivate


## Plain Python

Install virtualenv and create the environment called sitkpy.

    sudo pip install virtualenv
    virtualenv ~/sitkpy --no-site-packages

Install all of the required packages and SimpleITK, and activate the ipywidgets notebook extension.

    ~/sitkpy/bin/pip install -r Python/requirements.txt
    jupyter nbextension enable --py --sys-prefix widgetsnbextension

The requirements.txt file just lists the required packages ([see](requirements.txt)).


### Downloading Data

The data is automatically downloaded to the "Data" directory when you execute the notebooks.

Alternatively, to download all the data before hand:

    cd SimpleITK-Notebooks
    Utilities/downloaddata.py Data/ Data/manifest.json

### Run the notebooks

To launch:

    cd SimpleITK-Notebooks/Python
    ~/sitkpy/bin/jupyter notebook

### Working offline

In some situations, such as a tutorial session, you may not have internet access. This requires that you:

1. Download the data in advance - see above.

# View Static Converted Pages

Static views of all pages are available on the [html site of this repository](https://insightsoftwareconsortium.github.io/SimpleITK-Notebooks/).
