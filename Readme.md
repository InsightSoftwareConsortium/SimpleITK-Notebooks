# SimpleITK Notebooks

This is a collection of IPython Notebooks, designed for tutorials, presentations and demonstration of using SimpleITK in the "pylab" environment for interactive image process.

[SimpleITK](http://www.simpleitk.org) is an abstraction layer and wrapper around the [Insight Toolkit](http://www.itk.org) for many languages including python.


# Getting Started

For general information about installing SimpleITK please see the [SimpleITK wiki](http://www.itk.org/Wiki/ITK/Release_4/SimpleITK/GettingStarted).

## Additional Data Download

Additionally the SPL's "Multi-modality MRI-based Atlas of the Brain" should be downloaded and extracted into the SimpleITK-Notebooks/Data directory.

http://www.spl.harvard.edu/publications/item/view/2037


## Setting Up a Python Environment

It is recommended to setup a separate Python virtual environment to run through these notebooks as a tutorial.

Under the best of circumstances (tested on OSX 10.8 and 10.7.5, RH6, Ubuntu 12) this environment can be setup with the following:

    sudo pip install virtualenv
    virtualenv ~/sitkpy --no-site-packages
    ~/sitkpy/bin/pip install ipython
    ~/sitkpy/bin/pip install ipython[zmq]
    ~/sitkpy/bin/pip install tornado
    ~/sitkpy/bin/pip install numpy
    ~/sitkpy/bin/pip install matplotlib

Note: On Linux platforms you may be able to obtain many of these packages as system packages which may suffice ( Ubuntu 12+).
Note: On Window platforms some of these packages should be obtained as binary downloads and installed.

### Install SimpleITK

For many common platforms, a built distribution is available as an Python egg. This can be downloading and installed with the following command:

    ~/sitkpy/bin/easy_install SimpleITK
 

As of this writing, SimpleITK version >=0.6r1 is required to run these notebooks. This version currently needs to be downloaded from [Source Forge](http://sourceforge.net/projects/simpleitk/files/SimpleITK/0.6.rc1/Python/)


### Run the environment
 
To launch:

    cd SimpleITK-Notebooks
    ~/sitkpy/bin/ipython notebook --pylab=inline
