# SimpleITK Notebooks

[SimpleITK](http://www.simpleitk.org) is an abstraction layer and wrapper around the [Insight Toolkit](http://www.itk.org) for many languages including Python, R,...

This repository contains a collection of Jupyter Notebooks, designed for tutorials and  presentations and to demonstrate the use of SimpleITK for interactive image analysis.

The majority of the notebooks are written in Python, with some examples in R which are found, not surprisingly, in the R subdirectory. 


# View Static Converted Pages

- [00 Setup](http://insightsoftwareconsortium.github.io/SimpleITK-Notebooks/00_Setup.html)
- [01 Image Basics](http://insightsoftwareconsortium.github.io/SimpleITK-Notebooks/01_Image_Basics.html)
- [02 Pythonic Image](http://insightsoftwareconsortium.github.io/SimpleITK-Notebooks/02_Pythonic_Image.html)
- [03 Image Details](http://insightsoftwareconsortium.github.io/SimpleITK-Notebooks/03_Image_Details.html)
- [10 matplotlib's imshow](http://insightsoftwareconsortium.github.io/SimpleITK-Notebooks/10_matplotlib's_imshow.html)
- [20 Expand With Interpolators](http://insightsoftwareconsortium.github.io/SimpleITK-Notebooks/20_Expand_With_Interpolators.html)
- [21 Transforms and Resampling](http://insightsoftwareconsortium.github.io/SimpleITK-Notebooks/21_Transforms_and_Resampling.html)
- [22 Transforms](http://insightsoftwareconsortium.github.io/SimpleITK-Notebooks/22_Transforms.html)
- [30 Segmentation Region Growing](http://insightsoftwareconsortium.github.io/SimpleITK-Notebooks/30_Segmentation_Region_Growing.html)
- [31 Levelset Segmentation](http://insightsoftwareconsortium.github.io/SimpleITK-Notebooks/31_Levelset_Segmentation.html)
- [32 Watershed Segmentation](http://insightsoftwareconsortium.github.io/SimpleITK-Notebooks/32_Watersheds_Segmentation.html)
- [33 Thresholding and Edge Detection Segmentation](http://insightsoftwareconsortium.github.io/SimpleITK-Notebooks/33_Segmentation_Thresholding_Edge_Detection.html)
- [34 Segmentation Evaluation](http://insightsoftwareconsortium.github.io/SimpleITK-Notebooks/34_Segmentation_Evaluation.html)
- [41 Progress](http://insightsoftwareconsortium.github.io/SimpleITK-Notebooks/41_Progress.html)
- [55 Visible Human Resample](http://insightsoftwareconsortium.github.io/SimpleITK-Notebooks/55_VH_Resample.html)
- [56 Visible Human Registration 1](http://insightsoftwareconsortium.github.io/SimpleITK-Notebooks/56_VH_Registration1.html)
- [60 Registration Introduction](http://insightsoftwareconsortium.github.io/SimpleITK-Notebooks/60_Registration_Introduction.html)
- [61 Registration Introduction Continued](http://insightsoftwareconsortium.github.io/SimpleITK-Notebooks/61_Registration_Introduction_Continued.html)
- [62 Registration Tuning](http://insightsoftwareconsortium.github.io/SimpleITK-Notebooks/62_Registration_Tuning.html)
- [63 Registration Initialization](http://insightsoftwareconsortium.github.io/SimpleITK-Notebooks/63_Registration_Initialization.html)
- [64 Registration Memory Time Tradeoff](http://insightsoftwareconsortium.github.io/SimpleITK-Notebooks/64_Registration_Memory_Time_Tradeoff.html)
- [65 Registration Free Form Deformation](http://insightsoftwareconsortium.github.io/SimpleITK-Notebooks/65_Registration_FFD.html)
- [66 Registration Demons](http://insightsoftwareconsortium.github.io/SimpleITK-Notebooks/66_Registration_Demons.html)
- [67 Registration Homework](http://insightsoftwareconsortium.github.io/SimpleITK-Notebooks/67_Registration_Semiautomatic_Homework.html)

# Getting Started

For general information about installing SimpleITK please see the [SimpleITK wiki](http://www.itk.org/Wiki/ITK/Release_4/SimpleITK/GettingStarted).


## Setting Up a Python Environment

It is recommended to setup a separate Python virtual environment to run through these notebooks as a tutorial.

### Install Tutorial Dependencies

Under the best of circumstances (tested on OSX 10.8 and 10.7.5, RH6, Ubuntu 12) this environment can be setup with the following:

    sudo pip install virtualenv
    virtualenv ~/sitkpy --no-site-packages
    ~/sitkpy/bin/pip install 'ipython[all]' numpy matplotlib ipywidgets

Note: On Linux platforms you may be able to obtain many of these packages as system packages which may suffice ( Ubuntu 12+).
Note: On Window platforms some of these packages should be obtained as binary downloads and installed.

### Install SimpleITK

For many common platforms, a built distribution is available as an Python egg. This can be downloading and installed with the following command:

    ~/sitkpy/bin/easy_install SimpleITK


As of this writing, SimpleITK version >=0.9.0 is required to run these notebooks. This version currently needs to be downloaded from [Source Forge](http://sourceforge.net/projects/simpleitk/files/SimpleITK/0.9.0/Python/)

### Downloading Data

The data can be automatically downloaded to the "Data" directory when you execute the notebooks.

Alternatively, to download all the data before hand:

    cd SimpleITK-Notebooks
    ./downloaddata.py Data/ Data/manifest.json

### Run the environment

To launch:

    cd SimpleITK-Notebooks
    ~/sitkpy/bin/ipython notebook

### Working offline

In some situations, such as a tutorial session, you may not have internet access. This requires that you:

1. Download the data in advance - see above.
