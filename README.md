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

1. Language specific details for installing the notebooks is given in the README files in the respective directories ([Python](Python/README.md), [R](R/README.md)). For general information about installing SimpleITK please see the [SimpleITK read-the-docs](https://simpleitk.readthedocs.io/en/master/) pages.

2. The [SimpleITK API documentation](https://itk.org/SimpleITKDoxygen/html/index.html) is based on the C++ implementation which is readily mapped to your language of choice.

3. Learn the general concepts underlying the implementations of segmentation and registration by reading the ([ITK book](https://itk.org/ItkSoftwareGuide)). The relevant portion is "Book 2: Design and Functionality". The ITK API is significantly different from the SimpleITK one, but the general concepts are the same (e.g. combination of optimizer and similarity metric for registration).     

# Kicking the Tires

Before you clone the repository to your computer you may want to try it out, kick the tires so to speak.

Thanks to the awesome people from the [Binder Project](https://github.com/jupyterhub/binderhub)
you can try out the Python notebooks without installing a thing.

Some caveats:

1. This free service is currently in beta, so may not always be available.
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

If you are interested in the details, you can freely read the paper [here](http://em.rdcu.be/wf/click?upn=KP7O1RED-2BlD0F9LDqGVeSIWDx8-2B-2B8r81HkSA5fUW53U-3D_kZYp45lAKoeuSXKlMMKnLRu-2FO1jcvtAwo2UFz30PH9bPLAejS1IjjDkfGx8EIWfnvmrgAH2RF3xvrb1fezqultdVNEEAM7Fc2RGY-2BOVhjR-2BAN-2B7Wi6qUoM6BYtn1ZWsTzFdNZQxBXXJ2Nf0BaU5NhQLQVs2hoM2TXsKZ7pnKQXZVJEAOyLbQSvZkJOvdc7Gk36rdNDa3pn5vH17-2FvszYj4mKlZlgROxTE-2Be2yQ-2FOLAYsoDHZNvVuG4vJr4xNpQnmAI16Nz8h3GJi-2F9GKnpBsAg-3D-3D.).
