# SimpleITK Python Notebooks

As of this writing, SimpleITK version >=2.2.0 or newer is required to run these notebooks. This version is available from [PyPi](https://pypi.python.org/pypi/SimpleITK) and [Conda Forge](https://anaconda.org/conda-forge/simpleitk).

## Setting Up a Python Environment

We recommend setting up a separate Python virtual environment to run through these notebooks as a tutorial. Use either the Anaconda Python distribution or a plain Python distribution.

### Anaconda
With [Anaconda](https://www.anaconda.com/docs/main) you can set up a virtual environment, named sitkpy, and install all dependencies including SimpleITK using a single command:
```
conda env create -f environment.yml
```
**Run the notebooks**

To launch:
```
conda activate sitkpy
jupyter notebook
```

To deactivate the conda environment:
```
conda deactivate
````

### Plain Python

Create the virtual environment called sitkpy.
```
python -m venv sitkpy
```

Activate the virtual environment:  
On windows: ```sitkpy\Scripts\activate.bat```  
On linux/osx: ```source sitkpy/bin/activate```

Install all of the required packages.
```
pip install -r Python/requirements.txt
```

On Jupyter Notebooks version 5.2 or older activate the ipywidgets notebook extension:
```
jupyter nbextension enable --py --sys-prefix widgetsnbextension
```

The requirements.txt file lists the required packages ([see here](requirements.txt)).

**Run the notebooks**

To launch:  
Activate the virtual environment as above and:
```
jupyter notebook
```

## Downloading Data

The data is automatically downloaded to the "Data" directory when you execute the notebooks.

In some situations, such as a tutorial session, you may not have internet access. This requires that you download all the data before hand:
```
cd SimpleITK-Notebooks
Utilities/downloaddata.py Data/ Data/manifest.json
```