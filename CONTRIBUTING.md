# Contributions from the Community

We follow the standard GitHub [fork and pull request workflow](https://guides.github.com/activities/forking/).

## Adding/Modifying Code

Before you start working we recommend that you configure the environment to allow
you to test your modifications. If you do not install the testing packages or if you
forgot to run the tests on your system (happened to us more than once), don't
worry. All changes are tested when the pull request is issued. So while we trust
code is tested on the local system the continuous integration testing will
verify it before we merge it into the main repository.

### Setup for Testing

We use the [pytest](https://docs.pytest.org) Python testing framework as our test
driver for both the Python and R notebooks. Testing relies on several Python
packages listed in the [requirements_dev.txt](requirements_dev.txt) file. Please
install these packages. Note that we use the pyenchant
spell checker which is only available by using the pip package manager
(no conda). This spell checker relies on the [enchant](https://abiword.github.io/enchant/) library (`brew install enchant`,  `sudo apt-get install enchant`).  

When you add a new notebook, you will need to add it to the relevant list of
notebooks found in the [test_notebooks.py](tests/test_notebooks.py). These
are given as parameterizations to two methods `test_python_notebook` and
`test_r_notebook`. You can then run the test from the command line using (depending on the language):

```
pytest -v --tb=short tests/test_notebooks.py::Test_notebooks::test_python_notebook[new_notebook.ipynb]
```

or

```
   pytest -v --tb=short tests/test_notebooks.py::Test_notebooks::test_r_notebook[new_notebook.ipynb]
```

After you tested the notebook and all went well, you will also need to test it using a configuration similar to that of the continuous integration testing environment. In that environment we do not have the Fiji viewer installed and it is memory constrained.
What this means is that you will need to define two environment variables and rerun the
test:

```
export SITK_SHOW_COMMAND=no_viewer
export SIMPLE_ITK_MEMORY_CONSTRAINED_ENVIRONMENT=1
```

### Intentional Errors

For educational purposes we also include intentional errors in our notebooks.
These will generate an exception, and we want to check that the expected exception
was indeed generated. To facilitate this behavior we add a tag, `simpleitk_error_expected`, into the notebook's JSON section describing the code cell. The value of the tag is a unique
substring which is part of the expected error message. For examples, see this
[Python notebook](Python/03_Image_Details.ipynb), or this [R notebook](R/R_style_image.ipynb) (select the `Raw` display option on GitHub to
see the JSON code).

In some cases, an error may be allowed but not required/expected. This is the situation
with cells that invoke the SimpleITK `Show` command. The function depends on the availability of an external viewer which may or may not be installed. We therefor add a tag, `simpleitk_error_allowed`, into the JSON section describing the code cell. If the code
cell generates an error we check that it matches the allowed error. Thus the execution
is successful if no error or the allowed error were generated, otherwise the test fails.


### Working in a memory constrained environment

In some cases the data you are working with may be too large for use in the testing environment,
but it will work just fine on a standard computer (more than 4Gb of RAM). To enable us
to test these notebooks we include the following line at the top of the notebook (depending
on your language):

```
%run setup_for_testing
```
or

```
source("setup_for_testing.R")
```

The code in these files will modify SimpleITK's ReadImage function so that after
reading it resamples the image and returns a smaller one (if the `SIMPLE_ITK_MEMORY_CONSTRAINED_ENVIRONMENT` environment variable is on).

As a side note, this function overriding is convenient during initial code development,
facilitating faster experimentation. Note though that parameter selection values used in
the image analysis workflow for the resampled images may be different from those appropriate for the images at full resolution.

For the interested readers, the relevant code is found in [setup_for_testing.py](Python/setup_for_testing.py) and [setup_for_testing.R](R/setup_for_testing.R).

## Adding data

Add an entry to the [manifest.json](Data/manifest.json) file found in the `Data` directory. Each entry consists of the file name which is referenced in the notebook
and the sha512 hash number of that file. You can also use an archive file (tar or zip), in which case you need to indicate it as an archive. Archives are automatically unarchived
after download. For files stored in a Girder
data repository this is all that is needed. Raw urls are also supported with the
url entry.

Example of a standard file stored in a Girder data repository:
```
"SimpleITK.jpg" : {
"sha512": "f1b5ce1bf9d7ebc0bd66f1c3bc0f90d9e9798efc7d0c5ea7bebe0435f173355b27df632971d1771dc1fc3743c76753e6a28f6ed43c5531866bfa2b38f1b8fd46"
}
```

Example of an archive file stored on a standard website:
```
"POPI/meta/00-P.mhd": {
 "url": "http://tux.creatis.insa-lyon.fr/~srit/POPI/Images/MetaImage/00-MetaImage.tar",
 "archive": "true",
 "sha512": "09fcb39c787eee3822040fcbf30d9c83fced4246c518a24ab14537af4b06ebd438e2f36be91e6e26f42a56250925cf1bfa0d2f2f2192ed2b98e6a9fb5f5069fc"
}
```
