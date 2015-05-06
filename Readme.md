# SimpleITK Notebooks

This is a collection of IPython Notebooks, designed for tutorials, presentations and to demonstrate using SimpleITK in the IPython Notebook with scipy environment for interactive image process.

[SimpleITK](http://www.simpleitk.org) is an abstraction layer and wrapper around the [Insight Toolkit](http://www.itk.org) for many languages including python.

# View Static Converted Pages

- [01 Image Basics](http://insightsoftwareconsortium.github.io/SimpleITK-Notebooks/01_Image_Basics.html) 
- [02 Pythonic Image](http://insightsoftwareconsortium.github.io/SimpleITK-Notebooks/02_Pythonic_Image.html)
- [10 plotlib's imshow](http://insightsoftwareconsortium.github.io/SimpleITK-Notebooks/10_matplotlib's_imshow.html)
- [20 Expand With Interpolators](http://insightsoftwareconsortium.github.io/SimpleITK-Notebooks/20_Expand_With_Interpolators.html)
- [21 Transform and Resampling](http://insightsoftwareconsortium.github.io/SimpleITK-Notebooks/21_Transform_and_Resampling.html)
- [30 Segmentation Region Growing](http://insightsoftwareconsortium.github.io/SimpleITK-Notebooks/30_Segmentation_Region_Growing.html)
- [31 Levelset Segmentation](http://insightsoftwareconsortium.github.io/SimpleITK-Notebooks/31_Levelset_Segmentation.html)
- [32 Watershed Segmentation](http://insightsoftwareconsortium.github.io/SimpleITK-Notebooks/32_Watersheds_Segmentation.html)
- [41 Progress](http://insightsoftwareconsortium.github.io/SimpleITK-Notebooks/41_Progress.html)
- [55 Visible Human Resample](http://insightsoftwareconsortium.github.io/SimpleITK-Notebooks/55_VH_Resample.html)
- [56 Visible Human Registration 1](http://insightsoftwareconsortium.github.io/SimpleITK-Notebooks/56_VH_Registration1.html)
- [56 Visible Human Registration 1](http://insightsoftwareconsortium.github.io/SimpleITK-Notebooks/56_VH_Registration1.html)
- [57 RIRE Registration](http://insightsoftwareconsortium.github.io/SimpleITK-Notebooks/57_RIRE_Registration1.html)

# Getting Started

For general information about installing SimpleITK please see the [SimpleITK wiki](http://www.itk.org/Wiki/ITK/Release_4/SimpleITK/GettingStarted).

## Additional Data Downloads

Additionally the SPL's "Multi-modality MRI-based Atlas of the Brain" should be downloaded and extracted into the SimpleITK-Notebooks/Data directory.

http://www.spl.harvard.edu/publications/item/view/2037


For the Visible Human Notebooks the data should be downloaded from the MIDAS server.

http://midas3.kitware.com/midas/folder/10410


## Setting Up a Python Environment

It is recommended to setup a separate Python virtual environment to run through these notebooks as a tutorial.

Under the best of circumstances (tested on OSX 10.8 and 10.7.5, RH6, Ubuntu 12) this environment can be setup with the following:

    sudo pip install virtualenv
    virtualenv ~/sitkpy --no-site-packages
    ~/sitkpy/bin/pip install ipython[all]
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
    ~/sitkpy/bin/ipython notebook
