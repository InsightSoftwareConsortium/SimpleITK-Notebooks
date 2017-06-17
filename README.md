# SimpleITK Notebooks
[![CircleCI](https://circleci.com/gh/InsightSoftwareConsortium/SimpleITK-Notebooks/tree/master.svg?style=svg)](https://circleci.com/gh/InsightSoftwareConsortium/SimpleITK-Notebooks/tree/master)

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

1. Language specific details for installing the notebooks is given in the README files in the respective directories ([Python](Python/README.md), [R](R/README.md)). For general information about installing SimpleITK please see the [SimpleITK wiki](http://www.itk.org/Wiki/ITK/Release_4/SimpleITK/GettingStarted).

2. The [SimpleITK API documentation](https://itk.org/SimpleITKDoxygen/html/index.html) is based on the C++ implementation which is readily mapped to your language of choice.

3. Learn the general concepts underlying the implementations of segmentation and registration by reading the ([ITK book](https://itk.org/ItkSoftwareGuide)). The relevant portion is "Book 2: Design and Functionality". The ITK API is significantly different from the SimpleITK one, but the general concepts are the same (e.g. combination of optimizer and similarity metric for registration).     

# Contributions from the Community

We encourage contributions from the community!!!

1. Report issues you encounter (compatibility/bugs) using the [GitHub issue reporting system](https://guides.github.com/features/issues/).
2. Contribute:
   1. bug fixes.
   2. improved versions of existing notebooks, both text and code.
   3. new notebooks.

Just follow the [standard GitHub workflow](https://guides.github.com/activities/forking/).
