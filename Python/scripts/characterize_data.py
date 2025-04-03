#! /usr/bin/env python
# =========================================================================
#
#  Copyright NumFOCUS
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0.txt
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
# =========================================================================

import SimpleITK as sitk
import pandas as pd
import numpy as np
import os
import sys
import time
import json
import shutil
import subprocess
import concurrent.futures
from tqdm import tqdm
import platform
import copy
import matplotlib.pyplot as plt
from functools import partial
import argparse
import hashlib
import tempfile
from collections import defaultdict


# Datatypes with lightweight validation for use with argparse
def dir_path(path):
    if os.path.isdir(path):
        return path
    raise argparse.ArgumentTypeError(
        f"Invalid argument ({path}), not a directory path or directory does not exist."
    )


def file_path(path):
    if os.path.isdir(path):
        raise argparse.ArgumentTypeError(f"Invalid argument ({path}), not a file path.")
    return path


def positive_int(i):
    res = int(i)
    if res > 0:
        return res
    raise argparse.ArgumentTypeError(f"Invalid argument ({i}), expected value > 0 .")


def load_optional_parameters(file_name, parser):
    """
    Loading optional argparse parameters from a JSON configuration file.
    The contents of the JSON dictionary are run through the parser so that
    they adhere to the same constraints as those imposed on the parameters
    provided on the commandline.

    Parameters
    ----------
    file_name (Union[str, Path]): Name of JSON configuration file.
    parser (argparse.Parser): Parser for the optional commandline parameters.
    """
    config_argv = []
    with open(file_name, "r") as fp:
        configuration_dict = json.load(fp)
        # Convert dictionary to equivalent commandline entries
        # prepend -- to keys as these are optional argparse parameters
        for key, val in configuration_dict.items():
            # boolean flags added only if they are true
            if type(val) == bool:
                if val:
                    config_argv.append(f"--{key}")
            elif type(val) != list:
                config_argv.append(f"--{key}")
                config_argv.append(str(val))
            # checking the list length so that errors in the file,
            # empty list, are ignored
            elif len(val) > 0:
                config_argv.append(f"--{key}")
                config_argv.extend([str(v) for v in val])
    # parse the arguments and store in local config_data namespace
    # calling parse_known_args and not parse_args so that unexpected arguments
    # are ignored. Using parse_args results in an error if there
    # are unexpected arguments.
    config_data, additional_args = parser.parse_known_args(config_argv, namespace=None)

    if additional_args:
        print(
            f"Warning: unexpected arguments found in configuration file ({additional_args})."
        )
    return vars(config_data)


#
# Formatter used to print the parser description information and the individual help strings for the
# commandline parameters. The description is printed as is, i.e. raw, without modifying its
# original formatting (spaces, newlines...) and the individual help strings for the parameters include
# the default value settings. This is a combination of two existing argparse formatters via multiple
# inheritance.
#
class RawDescriptionAndDefaultHelpFormatter(
    argparse.RawDescriptionHelpFormatter, argparse.ArgumentDefaultsHelpFormatter
):
    pass


def inspect_grayscale_image(sitk_image, image_info):
    np_arr_view = sitk.GetArrayViewFromImage(sitk_image)
    image_info["MD5 intensity hash"] = hashlib.md5(np_arr_view).hexdigest()
    mmfilter = sitk.MinimumMaximumImageFilter()
    mmfilter.Execute(sitk_image)
    image_info["min intensity"] = mmfilter.GetMinimum()
    image_info["max intensity"] = mmfilter.GetMaximum()
    image_info["mean intensity"] = np_arr_view.mean()
    image_info["std intensity"] = np_arr_view.std()
    # Potentially provide more complete information on intensity distribution:
    # skew (scipy.stats.skew, asymmetry around mean),
    # kurtosis (scipy.stats.kurtosis, how heavy are the distribution tails / how many outliers)
    # percentiles, [10,25,50,75,90] (np.percentile)
    # For now, not adding the dependency on scipy.stats or computational complexity of
    # percentile computations.


def inspect_image(sitk_image, image_info, meta_data_info, thumbnail_settings):
    """
    Inspect a SimpleITK image, and update the image_info dictionary with the values associated with the
    contents of the meta_data_info dictionary. The values of the image meta data dictionary keys are
    copied into the image_info dictionary (image_info[k] = sitk_image.GetMetaData(meta_data_info[k])).

    Parameters
    ----------
    sitk_image (SimpleITK.Image): Input image for inspection, 2D or 3D.
    image_info (dict): Image information is added to this dictionary (e.g. image_info["image size"] = "(512,512)").
                       The image_info dict is filled with the following values:
                           "MD5 intensity hash" - Enable identification of duplicate images in terms of intensity.
                                                  This is different from SimpleITK image equality where the
                                                  same intensities with different image spacing/origin/direction cosine
                                                  are considered different images as they occupy a different spatial
                                                  region.
                           Image spatial information - "image size", "image spacing", "image origin", "axis direction".
                           Image intensity information - "pixel type", if scalar or repeated scalar impersonating a
                                                          multi-channel image:"min", "max", "mean", "std".
                           metadata values for the values listed in the meta_data_info dictionary (e.g. "radiographic view" : "AP").
    meta_data_info(dict(str:str)): The meta-data information whose values will be reported.
                                   Dictionary structure is description:meta_data_tag
                                   (e.g. {"radiographic view" : "0018|5101", "modality" : "0008|0060",
                                          "ITK_InputFilterName" : "ITK_InputFilterName"}).
    thumbnail_settings(dict): Dictionary containing the following keys "thumbnail_sizes", "projection_axis" and
                              "interpolator" which are used to create a thumbnail representing this image that is
                              stored in image_info["thumbnail"].
    """
    np_arr_view = sitk.GetArrayViewFromImage(sitk_image)
    image_info["image size"] = sitk_image.GetSize()
    image_info["image spacing"] = sitk_image.GetSpacing()
    image_info["image origin"] = sitk_image.GetOrigin()
    image_info["axis direction"] = sitk_image.GetDirection()

    if (
        sitk_image.GetNumberOfComponentsPerPixel() == 1
    ):  # grayscale image, get measures of intensity location and spread the min/max pixel values
        image_info["pixel type"] = sitk_image.GetPixelIDTypeAsString() + " gray"
        inspect_grayscale_image(sitk_image, image_info)
    else:  # either a color image or a grayscale image masquerading as a color one
        pixel_type = sitk_image.GetPixelIDTypeAsString()
        channels = [
            sitk.VectorIndexSelectionCast(sitk_image, i)
            for i in range(sitk_image.GetNumberOfComponentsPerPixel())
        ]
        # if this multi-channel is actually a grayscale image, treat
        # it as such, call inspect_grayscale_image on the first channel
        # this will compute the intensity statistics and the md5 hash on
        # the actual grayscale information
        if np.array_equal(
            sitk.GetArrayViewFromImage(channels[0]),
            sitk.GetArrayViewFromImage(channels[1]),
        ) and np.array_equal(
            sitk.GetArrayViewFromImage(channels[0]),
            sitk.GetArrayViewFromImage(channels[2]),
        ):
            pixel_type = (
                pixel_type
                + f" {sitk_image.GetNumberOfComponentsPerPixel()} channels gray"
            )
            inspect_grayscale_image(channels[0], image_info)
        else:
            image_info["MD5 intensity hash"] = hashlib.md5(np_arr_view).hexdigest()
            pixel_type = (
                pixel_type
                + f" {sitk_image.GetNumberOfComponentsPerPixel()} channels color"
            )
        image_info["pixel type"] = pixel_type
    img_keys = sitk_image.GetMetaDataKeys()
    for k, v in meta_data_info.items():
        if v in img_keys:
            image_info[k] = sitk_image.GetMetaData(v)
    if thumbnail_settings:
        image_info["thumbnail"] = image_to_thumbnail(sitk_image, **thumbnail_settings)


def inspect_single_file(
    file_name,
    imageIO="",
    meta_data_info={},
    external_programs_info={},
    thumbnail_settings={},
):
    """
    Inspect a file using the specified imageIO, returning a dictionary with the relevant information.

    Parameters
    ----------
    file_name (str): Image file name.
    imageIO (str): Name of image IO to use. To see the list of registered image IOs use the
                   ImageFileReader::GetRegisteredImageIOs() or print an ImageFileReader.
                   The empty string indicates to read all file formats supported by SimpleITK.
    meta_data_info(dict(str:str)): The meta-data information whose values will be reported.
                                   Dictionary structure is description:meta_data_tag
                                   (e.g. {"radiographic view" : "0018|5101", "modality" : "0008|0060"}).
    external_programs_info(dict(str:str)): A dictionary of programs that are run with the file_name as input
                                  the return value 'succeeded' or 'failed' is recorded. This
                                  is useful for example if you need to validate conformance
                                  to a standard such as DICOM. Dictionary format is description:program (e.g.
                                  {"DICOM compliant" : "path_to_dicom3tools/dciodvfy"}).
    thumbnail_settings(dict): A dictionary containing the settings required for creating a 2D thumbnail.
                              from an image. These include thumbnail_sizes (x,y size of thumbnail),
                              projection axis (maximal intensity project 3D images along this axis and
                              then create the 2D thumbnail from the projection), interpolator (SimpleITK
                              interpolator used to resize the 2D image to the thumbnail size).

    Returns
    -------
     dict with the following entries: files, MD5 intensity hash,
                                       image size, image spacing, image origin, axis direction,
                                       pixel type, min intensity, max intensity, mean intensity,
                                       std intensity,
                                       meta data_1...meta_data_n,
                                       external_program_res_1...external_program_res_m
    If the given file is not readable by SimpleITK, the only entry in the dictionary
    will be the "files" entry.
    """
    # Using a list so that returned csv is consistent with the series based analysis (an
    # image is defined by multiple files).
    file_info = {}
    file_info["files"] = [file_name]
    try:
        reader = sitk.ImageFileReader()
        reader.SetImageIO(imageIO)
        reader.SetFileName(file_name)
        img = reader.Execute()
        inspect_image(img, file_info, meta_data_info, thumbnail_settings)
        for k, p in external_programs_info.items():
            try:
                # run the external programs, check the return value, and capture all output so it
                # doesn't appear on screen. The CalledProcessError exception is raised if the
                # external program fails (returns non zero value).
                subprocess.run([p, file_name], check=True, capture_output=True)
                file_info[k] = "succeeded"
            except Exception:
                file_info[k] = "failed"
    except Exception:
        pass
    return file_info


def inspect_files(
    root_dir,
    max_processes,
    disable_tqdm,
    imageIO="",
    meta_data_info={},
    external_programs_info={},
    thumbnail_settings={},
):
    """
    Iterate over a directory structure and return a pandas dataframe with the relevant information for the
    image files. This also includes non image files. The resulting dataframe will only include the file name
    if that file wasn't successfully read by SimpleITK. The two reasons for failure are: (1) the user specified
    imageIO isn't compatible with the file format (e.g. user is only interested in reading jpg and the file
    format is mha) or (2) the file could not be read by the SimpleITK IO (corrupt file or unexpected limitation of
    SimpleITK).

    Parameters
    ----------
    root_dir (str): Path to the root of the data directory. Traverse the directory structure
                    and inspect every file (also report non image files, in which
                    case the only valid entry will be the file name).
    max_processes (int): Maximal number of processes to use in when performing parallel processing.
                         Only relevant for non-windows systems.
    disable_tqdm (bool): Display a progress bar, or not.
    imageIO (str): Name of image IO to use. To see the list of registered image IOs use the
                   ImageFileReader::GetRegisteredImageIOs() or print an ImageFileReader.
                   The empty string indicates to read all file formats supported by SimpleITK.
    meta_data_info(dict(str:str)): The meta-data information whose values will be reported.
                                   Dictionary structure is description:meta_data_tag
                                   (e.g. {"radiographic view" : "0018|5101", "modality" : "0008|0060"}).
    external_programs_info(dict(str:str)): A dictionary of programs that are run with the file_name as input
                                  the return value 'succeeded' or 'failed' is recorded. This
                                  is useful for example if you need to validate conformance
                                  to a standard such as DICOM. Dictionary format is description:program (e.g.
                                  {"DICOM compliant" : "path_to_dicom3tools/dciodvfy"}).
    thumbnail_settings(dict): A dictionary containing the settings required for creating a 2D thumbnail.
                              from an image. These include thumbnail_sizes (x,y size of thumbnail),
                              projection axis (maximal intensity project 3D images along this axis and
                              then create the 2D thumbnail from the projection), interpolator (SimpleITK
                              interpolator used to resize the 2D image to the thumbnail size).
    Returns
    -------
    pandas DataFrame: Each row in the data frame corresponds to a single file.
    """
    all_file_names = []
    for dir_name, subdir_names, file_names in os.walk(root_dir):
        all_file_names += [
            os.path.join(os.path.abspath(dir_name), fname) for fname in file_names
        ]

    # Get list of dictionaries describing the results and then combine into a dataframe, faster
    # than appending to the dataframe one by one. Use parallel processing to speed things up.
    res = []
    with concurrent.futures.ProcessPoolExecutor(max_processes) as executor:
        futures = (
            executor.submit(
                partial(
                    inspect_single_file,
                    imageIO=imageIO,
                    meta_data_info=meta_data_info,
                    external_programs_info=external_programs_info,
                    thumbnail_settings=thumbnail_settings,
                ),
                file_name,
            )
            for file_name in all_file_names
        )
        # tqdm configuration, set miniters (minimal number of iterations before updating the progress bar) to
        # be about ~10% of data in combination with maxinterval of 60sec. If the 10% interval takes more
        # than 60sec then tqdm automatically changes it to match the maxinterval. Additionally, the whole progress
        # bar is disabled if disable_tqdm is True, for example when scheduling a job on a cluster in which case there
        # is no person looking at the progress.
        tqdm_total = len(all_file_names)
        for file_name, future in tqdm(
            zip(all_file_names, concurrent.futures.as_completed(futures)),
            total=tqdm_total,
            maxinterval=60,
            miniters=tqdm_total // 10,
            disable=disable_tqdm,
            file=sys.stdout,
        ):
            try:
                result = future.result()
                res.append(result)
            except Exception as e:
                print(f"Failed process for {file_name}", file=sys.stderr)
    return pd.DataFrame.from_dict(res)


def inspect_single_series(series_data, meta_data_info={}, thumbnail_settings={}):
    """
    Inspect a single DICOM series (DICOM hierarchy of patient-study-series-image).
    This can be a single file, or multiple files such as a CT or MR volume.

    Parameters
    ----------
    series_data (two entry tuple): First entry is series:study...(DICOM tag values uniquely identifying series),
                                   second entry is the list of files comprising this series.
    meta_data_info(dict(str:str)): The meta-data information whose values will be reported.
                                   Dictionary structure is description:meta_data_tag
                                   (e.g. {"radiographic view" : "0018|5101", "modality" : "0008|0060"}).
    Returns
    -------
     dictionary containing all of the information about the series.
    """
    series_info = {}
    series_info["files"] = series_data[1]
    try:
        reader = sitk.ImageSeriesReader()
        reader.MetaDataDictionaryArrayUpdateOn()
        reader.LoadPrivateTagsOn()
        # split list of tag values, sid is first entry (see inspect_series)
        sid = series_data[0].split(":")[0]
        file_names = series_info["files"]
        # As the files comprising a series can reside in separate directories
        # and may have identical file names (e.g. 1/Z0.dcm, 2/Z0.dcm)
        # we use a tempdir and symbolic links to enable SimpleITK to read the series as
        # a single image (ImageSeriesReader_GetGDCMSeriesFileNames expects all files to
        # be in a single directory).
        # On Windows we need to copy the files to the tempdir as the os.symlink documentation says that
        # "On newer versions of Windows 10, unprivileged accounts can create symlinks
        # if Developer Mode is enabled. When Developer Mode is not available/enabled,
        # the SeCreateSymbolicLinkPrivilege privilege is required, or the process must be
        # run as an administrator."
        # To turn Developer Mode on in Windows 11:
        # Settings->System->For Developers and turn Developer Mode on.
        # We could then use the os.symlink function instead of the indirect usage of a
        # copy_link_function below.
        with tempfile.TemporaryDirectory() as tmpdirname:
            copy_link_function = (
                shutil.copy if platform.system() == "Windows" else os.symlink
            )
            new_orig_file_name_dict = {}
            for i, fname in enumerate(file_names):
                new_fname = os.path.join(tmpdirname, str(i))
                new_orig_file_name_dict[new_fname] = fname
                copy_link_function(fname, new_fname)
            # On windows the returned full paths use backslash
            # for all directories except the last one which has a slash. This does not
            # match the contents of the new_orig_file_name_dict which has a backslash
            # for the last entry too, as expected on windows. This is an issue with GDCM
            # and we reported it on its bug tracker. In the code below we call os.path.normpath to
            # resolve this issue.
            sorted_new_file_names = sitk.ImageSeriesReader_GetGDCMSeriesFileNames(
                tmpdirname, sid
            )
            # store the file names in a sorted order so that they are saved in this
            # manner. This is useful for reading from the saved csv file
            # using the SeriesImageReader or ImageRead which expect ordered file names
            series_info["files"] = [
                new_orig_file_name_dict[os.path.normpath(new_fname)]
                for new_fname in sorted_new_file_names
            ]
            reader.SetFileNames(sorted_new_file_names)
            img = reader.Execute()
            for k in meta_data_info.values():
                if reader.HasMetaDataKey(0, k):
                    img.SetMetaData(k, reader.GetMetaData(0, k))
            inspect_image(img, series_info, meta_data_info, thumbnail_settings)
    except Exception:
        pass
    return series_info


def get_series_key_fname(file_name, additional_series_tags):
    """
    If a DICOM file, create a unique string identifier representing its series. This is
    a combination of the series UID, study UID and the values of the additional series
    tags. For non DICOM files or files that GDCM cannot read this function will raise
    an exception.

    Parameters
    ----------
    file_name (Union[str,Path]): Name of file.
    additional_series_tags (list(str)): List of DICOM tags that together with
    series and study UID serve to uniquely identify files belonging to the same
    series.

    Returns
    -------
    A tuple (key, file_name) where key is a unique identifier string
    comprised of series UID:study UID:values from additional series tags. This
    will succeed if the given file_name is a DICOM file that GDCM can read,
    if not an exception is raised by the ImageFileReader.
    """
    reader = sitk.ImageFileReader()
    # explicitly set ImageIO to GDCMImageIO so that non DICOM files that
    # contain DICOM tags (file converted from original DICOM) will be
    # ignored.
    reader.SetImageIO("GDCMImageIO")
    reader.SetFileName(file_name)
    reader.ReadImageInformation()
    sid = reader.GetMetaData("0020|000e")
    study = reader.GetMetaData("0020|000d")
    key = f"{sid}:{study}"
    key += ":".join(
        [
            reader.GetMetaData(k) if reader.HasMetaDataKey(k) else " "
            for k in additional_series_tags
        ]
    )
    return (key, file_name)


def inspect_series(
    root_dir,
    max_processes,
    disable_tqdm,
    additional_series_tags,
    meta_data_info={},
    thumbnail_settings={},
):
    """
    Inspect all series found in the directory structure. A series does not have to
    be in a single directory (the files are located in the subtree and combined
    into a single image).

    Parameters
    ----------
    root_dir (str): Path to the root of the data directory. Traverse the directory structure
                    and inspect every series. If the series is comprised of multiple image files
                    they do not have to be in the same directory. The only expectation is that all
                    images from the series are under the root_dir.
    max_processes (int): Maximal number of processes to use in when performing parallel processing.
                         Only relevant for non-windows systems.
    disable_tqdm (bool): Display a progress bar, or not.
    additional_series_tags list(str): List of DICOM tags used to uniquely identify files belonging to the same
                          series. These are in addition to 0020|000e, series instance UID, and
                          0020|000d, study Instance UID that are always used.
    meta_data_info(dict(str:str)): The meta-data information whose values will be reported.
                                   Dictionary structure is description:meta_data_tag
                                   (e.g. {"radiographic view" : "0018|5101", "modality" : "0008|0060"}).
    thumbnail_settings(dict): A dictionary containing the settings required for creating a 2D thumbnail.
                              from an image. These include thumbnail_sizes (x,y size of thumbnail),
                              projection axis (maximal intensity project 3D images along this axis and
                              then create the 2D thumbnail from the projection), interpolator (SimpleITK
                              interpolator used to resize the 2D image to the thumbnail size).
    Returns
    -------
    pandas DataFrame: Each row in the data frame corresponds to a single series.
    """
    # Identify all files that belong to the same DICOM series. The all_series_files dictionary keys
    # are unique series identifiers and the values are lists of files belonging
    # to the corresponding series.
    # Use the collections defaultdict so we can call all_series_files[key].append()
    # without a key error. If the key doesn't exist, it is created with an empty list and the
    # value is added to that list.
    # First obtain all files in the directory structure, then concurrently obtain a key representing
    # the series if it is a DICOM file. The key is based on combining the series and study UIDs and
    # the values corresponding to the provided additional_series_tags.
    all_series_files = defaultdict(list)
    all_file_names = []
    for dir_name, subdir_names, file_names in os.walk(root_dir):
        all_file_names += [
            os.path.join(os.path.abspath(dir_name), fname) for fname in file_names
        ]
    with concurrent.futures.ProcessPoolExecutor(max_processes) as executor:
        futures = (
            executor.submit(
                partial(
                    get_series_key_fname,
                    additional_series_tags=additional_series_tags,
                ),
                file_name,
            )
            for file_name in all_file_names
        )
        for future in concurrent.futures.as_completed(futures):
            # if an exception was thrown by the process, for example the file is not in DICOM
            # format then it will be re-raised when attempting to access the future's
            # result, we can ignore it.
            try:
                result = future.result()
                all_series_files[result[0]].append(result[1])
            except Exception as e:
                pass

    # Get list of dictionaries describing the results and then combine into a dataframe, faster
    # than appending to the dataframe one by one.
    res = []
    with concurrent.futures.ProcessPoolExecutor(max_processes) as executor:
        futures = (
            executor.submit(
                partial(
                    inspect_single_series,
                    meta_data_info=meta_data_info,
                    thumbnail_settings=thumbnail_settings,
                ),
                series_data,
            )
            for series_data in all_series_files.items()
        )
        # tqdm configuration, set miniters (minimal number of iterations before updating the progress bar) to
        # be about ~10% of data in combination with maxinterval of 60sec. If the 10% interval takes more
        # than 60sec then tqdm automatically changes it to match the maxinterval. Additionally, the whole progress
        # bar is disabled if disable_tqdm is True, for example when scheduling a job on a cluster in which case there
        # is no person looking at the progress.
        tqdm_total = len(all_series_files)
        for file_names, future in tqdm(
            zip(all_series_files.values(), concurrent.futures.as_completed(futures)),
            total=tqdm_total,
            maxinterval=60,
            miniters=tqdm_total // 10,
            disable=disable_tqdm,
            file=sys.stdout,
        ):
            try:
                result = future.result()
                res.append(result)
            except Exception as e:
                print(f"Failed process for {file_names}", file=sys.stderr)
    return pd.DataFrame.from_dict(res)


def image_to_thumbnail(img, thumbnail_sizes, interpolator, projection_axis):
    """
    Create a grayscale thumbnail image from the given image. If the image is 3D it is
    projected to 2D using a Maximum Intensity Projection (MIP) approach. Color images
    are converted to grayscale, and high dynamic range images are window leveled using
    a robust estimate of the relevant minimum and maximum intensity values.

    Parameters
    ----------
    img (SimpleITK.Image): A 2D or 3D grayscale or sRGB image.
    thumbnail_sizes (list/tuple(int)): The 2D sizes of the thumbnail.
    interpolator: Interpolator to use when resampling to a thumbnail. Nearest neighbor
                  is computationally efficient and is applicable for
                  both segmentation masks and scalar images.
    projection_axis(int in [0,2]): The axis along which we project 3D images.

    Returns
    -------
    2D SimpleITK image with sitkUInt8 pixel type.
    """
    if (
        img.GetDimension() == 3 and img.GetSize()[2] == 1
    ):  # 2D image masquerading as 3D image
        img = img[:, :, 0]
    elif img.GetDimension() == 3:  # 3D image projected along projection_axis direction
        img = sitk.MaximumProjection(img, projection_axis)
        slc = list(img.GetSize())
        slc[projection_axis] = 0
        img = sitk.Extract(img, slc)
    # convert multi-channel image to gray
    # sRGB, sRGBA or image with more than 4 channels. assume the first three channels represent
    # RGB. when there are more than 4 channels this assumption is likely incorrect, but there's
    # nothing more sensible to do. maybe select an arbitrary channel but that is problematic
    # if the 4 channel image is sRGBA and A is 255, so selecting the last channel is just a "white" image.
    if img.GetNumberOfComponentsPerPixel() >= 3:
        # Convert image to gray scale and rescale results to [0,255]
        channels = [
            sitk.VectorIndexSelectionCast(img, i, sitk.sitkFloat32) for i in range(3)
        ]
        # linear mapping
        I = (
            1
            / 255.0
            * (0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2])
        )
        # nonlinear gamma correction
        I = (
            I * sitk.Cast(I <= 0.0031308, sitk.sitkFloat32) * 12.92
            + I ** (1 / 2.4) * sitk.Cast(I > 0.0031308, sitk.sitkFloat32) * 1.055
            - 0.055
        )
        img = sitk.Cast(sitk.RescaleIntensity(I), sitk.sitkUInt8)
    else:
        if img.GetPixelID() != sitk.sitkUInt8:
            # To deal with high dynamic range images that also contain outlier intensities
            # we use window-level intensity mapping and set the window:
            # to [max(Q1 - w*IQR, min_intensity), min(Q3 + w*IQR, max_intensity)]
            # IQR = Q3-Q1
            # The bounds which should exclude outliers are defined by the parameter w,
            # where 1.5 is a standard default value (same as used in box and
            # whisker plots to define whisker lengths).
            w = 1.5
            min_val, q1_val, q3_val, max_val = np.percentile(
                sitk.GetArrayViewFromImage(img).ravel(), [0, 25, 75, 100]
            )
            min_max = [
                np.max([(1.0 + w) * q1_val - w * q3_val, min_val]),
                np.min([(1.0 + w) * q3_val - w * q1_val, max_val]),
            ]
            wl_image = sitk.IntensityWindowing(
                img,
                windowMinimum=min_max[0],
                windowMaximum=min_max[1],
                outputMinimum=0.0,
                outputMaximum=255.0,
            )
            img = sitk.Cast(wl_image, sitk.sitkUInt8)
        else:  # pixel type of uint8
            img = sitk.IntensityWindowing(
                img,  # numpy returns its own type np.uint8 which isn't converted implicitly by SimpleITK
                windowMinimum=int(np.min(sitk.GetArrayViewFromImage(img))),
                windowMaximum=int(np.max(sitk.GetArrayViewFromImage(img))),
            )
    # Computations below are simplified if we assume image axes are the
    # standard basis. This is reasonable for the purpose of creating a
    # thumbnail, even when it does not match the actual image information.
    # We therefor enforce it here.
    img.SetDirection([1, 0, 0, 1])
    new_spacing = [
        ((osz - 1) * ospc) / (nsz - 1)
        for ospc, osz, nsz in zip(img.GetSpacing(), img.GetSize(), thumbnail_sizes)
    ]
    new_spacing = [max(new_spacing)] * img.GetDimension()
    center = img.TransformContinuousIndexToPhysicalPoint(
        [sz / 2.0 for sz in img.GetSize()]
    )
    new_origin = [
        c - c_index * nspc
        for c, c_index, nspc in zip(
            center, [sz / 2.0 for sz in thumbnail_sizes], new_spacing
        )
    ]
    # Usually, the defaultPixelValue is set to zero, but when this value
    # pads the image it is hard to separate the image from a viewer's
    # background which is usually also set to zero. We therefor set it to
    # 127, middle of the intensity range used for the thumbnail creation.
    res = sitk.Resample(
        img,
        size=thumbnail_sizes,
        transform=sitk.Transform(),
        interpolator=interpolator,
        outputOrigin=new_origin,
        outputSpacing=new_spacing,
        outputDirection=img.GetDirection(),
        defaultPixelValue=127,
        outputPixelType=img.GetPixelID(),
    )
    res.SetSpacing([1, 1])
    res.SetOrigin([0, 0])
    return res


def image_list_to_faux_volume(image_list, tile_size):
    """
    Create a faux volume from a list of images all having the same size.

    Parameters
    ----------
    image_list (list[SimpleITK.Image]): List of images all with the same size.
    tile_size([int,int]): The number of images in x and y in each faux volume slice.

    Returns
    -------
    3D SimpleITK image combining all the images contained in the image_list.
    """
    step_size = tile_size[0] * tile_size[1]
    faux_volume_slices = [
        sitk.Tile(image_list[i : i + step_size], tile_size, 0)
        for i in range(0, len(image_list), step_size)
    ]

    # if last tile image is smaller than others, add background content to match the size
    if len(faux_volume_slices) > 1 and (
        faux_volume_slices[-1].GetHeight() != faux_volume_slices[-2].GetHeight()
        or faux_volume_slices[-1].GetWidth() != faux_volume_slices[-2].GetWidth()
    ):
        image = sitk.Image(faux_volume_slices[-2]) * 0
        faux_volume_slices[-1] = sitk.Paste(
            image,
            faux_volume_slices[-1],
            faux_volume_slices[-1].GetSize(),
            [0, 0],
            [0, 0],
        )
    return sitk.JoinSeries(faux_volume_slices)


def characterize_data(argv=None):
    """
    This script inspects/characterizes images in a given directory structure. It
    recursively traverses the directories and either inspects the files one by one
    or if in DICOM series inspection mode, inspects the data on a per-series basis
    (e.g. combines all 2D images belonging to the same CT series into a single 3D image).

    Running:
    -------
    To run the script one has to specify:
        1. Root of the data directory.
        2. Filename of csv output, can include relative or absolute path.
        3. The analysis type to perform per_file or per_series. The latter indicates
           we are only interested in DICOM files.

    There are many additional optional parameters which control program behaviour.
    These include:
     1. A JSON configuration file that specifies user preferred default
        values for optional program parameters, overriding the hard coded
        defaults.
    2. Maximal number of processes to use for concurrent processing.
    3. User specified series tags used to identify files as belonging to the same
       DICOM series.
    4. A particular SimpleITK ImageIO class to use, limiting analysis to a particular
       image file format (e.g. BMPImageIO limits to BMP).
    5. External applications to run and corresponding headings used in the csv output.
       The external applications return value (zero or non zero) is used to log
       success or failure. A nice example is the dciodvfy program from David
       Clunie (https://www.dclunie.com/dicom3tools.html)
       which validates compliance with the DICOM standard.
    6. Metadata keys and corresponding headings used in the csv output. These are
       image specific keys such as DICOM tags or other metadata tags that may be
       found in the image. The content of the tags is written to the output csv file.
    7. A flag that indicates that problematic files should not be listed in the output csv.
    8. A flag indicating whether to create a summary image and additional parameters associated
       with the summary image. The summary image is a faux volume where each slice is composed
       of multiple 2D grayscale thumbnails representing the original images. When the original
       image is a color image it is converted to grayscale. When the original image is 3D
       it is converted to 2D via maximum intensity projection along a user specified axis. To
       retain the original image's aspect ratio it is resized and padded to fit in the user
       specified thumbnail size image.

    Examples:
    --------
    Run a generic file analysis:
    python characterize_data.py ../../Data/ Output/generic_image_data_report.csv per_file \
    --imageIO All --external_applications ./dciodvfy --external_applications_headings "DICOM Compliant" \
    --metadata_keys "0008|0060" "0018|5101" --metadata_keys_headings "modality" "radiographic view" \
    --max_processes 15

    Run a DICOM series based analysis:
    python characterize_data.py ../../Data/ Output/DICOM_image_data_report.csv per_series \
    --metadata_keys "0008|0060" "0018|5101" --metadata_keys_headings "modality" "radiographic view" \
    --max_processes 15

    Run a generic file analysis, omit problematic files from csv (--ignore_problems) and create a summary
    image which is composed of thumbnails from all the images.
    python characterize_data.py ../../Data/ Output/generic_image_data_report.csv per_file \
    --external_applications ./dciodvfy --external_applications_headings "DICOM compliant" \
    --metadata_keys "0008|0060" --metadata_keys_headings modality --ignore_problems --create_summary_image \
    --max_processes 15

    Run a generic file analysis using a configuration file and redirect stderr to file.
    python characterize_data.py ../../Data/ Output/generic_image_data_report.csv per_file \
    --configuration_file ../../Data/characterize_data_user_defaults.json 2> errors.txt

    Output:
    ------
    The output from the script includes:
        1. A csv file with columns containing basic information describing each image (an image
           may be one or multiple files).
        2. A JSON configuration file with the parameter settings used in the analysis (file name has
           a date-time prefix and "_characterize_data_settings.json" postfix). This file can then be
           used to override the default parameter settings with user defaults in a reproducible
           manner via the --configuration_file option.
        3. pdf figure with the histogram of image sizes.
        4. Possibly a pdf figure with histogram of min-max intensity values for the scalar images, if any.
        5. Possibly a csv file listing exact duplicate images, if any. Images are considered duplicates if
           the intensity values are the same, header and spatial information may be different.

    Empty lines in the resulting csv file (file names listed but nothing else in that row)
    occur when SimpleITK cannot read the file or set of files when dealing with a series.
    Specifically:
        a. The file is not in a recognized image format.
        b. The file is a corrupt image file.
        c. A SimpleITK imageIO was explicitly specified and it cannot read that file,
           e.g. specifying BMPImageIO and the file is in jpg format.
    These empty lines will not be included in the output csv if the
    --ignore_problems flag is set.

    NOTE: For the same directory structure, the order of the rows in the output csv file will vary
    across operating systems (order of files in the "files" column also varies). This is a consequence
    of using os.walk to traverse the file system (internally os.walk uses os.scandir and that method's
    documentation says "The entries are yielded in arbitrary order.").

    Convert from x, y, z (zero based) indexes from the "summary image" to information from
    "summary csv" file. To view the summary image and obtain the x-y-z coordinates for a
    specific thumbnail we recommend using one of the following free programs:
    Fiji (uses zero based indexing): https://imagej.net/software/fiji/
    3D slicer (uses zero based indexing): https://www.slicer.org/
    ITK-SNAP (uses one based indexing, subtract one): http://www.itksnap.org/


    import pandas as pd
    import SimpleITK as sitk

    def xyz_to_index(x, y, z, thumbnail_size, tile_size):
        return (z * tile_size[0] * tile_size[1]
                + int(y / thumbnail_size[1]) * tile_size[0]
                + int(x / thumbnail_size[0])
                )

    summary_csv_file_name =
    df = pd.read_csv(summary_csv_file_name)
    # Ensure dataframe matches the read images. If the report included files that
    # were not read (non-image or read failures) remove them.
    df.dropna(inplace=True, thresh=2)

    thumbnail_size =
    tile_size =
    print(df["files"].iloc[xyz_to_index(x, y, z, thumbnail_size, tile_size)])

    Caveat:
    ------
    When characterizing a set of DICOM images, start by running the script in per_file
    mode. This will identify duplicate image files. Remove them before running using the per_series
    mode. If run in per_series mode on the original data the duplicate files will not be identified
    as such, they will be identified as belonging to the same series. In this situation we end up
    with multiple images in the same spatial location (repeated 2D slice in a 3D volume). This will
    result in incorrect values reported for the spacing, image size etc.
    When this happens you will see a WARNING printed to the terminal output, along the lines of
    "ImageSeriesReader : Non uniform sampling or missing slices detected...".
    """
    # Configure argument parser for commandline arguments and set default
    # values.
    # We use two parsers, one for the optional parameters and the other for positional and
    # optional parameters. The former is given as a parent of the latter in the constructor.
    # This is required for reading the optional paramters from a configuration file.
    opt_arg_parser = argparse.ArgumentParser(add_help=False)
    opt_arg_parser.add_argument(
        "--configuration_file",
        type=file_path,
        help="JSON configuration file containing settings for the optional parameters",
    )
    opt_arg_parser.add_argument(
        "--max_processes",
        type=positive_int,
        default=2,
        help="maximal number of parallel processes",
    )
    opt_arg_parser.add_argument(
        "--disable_tqdm",
        action="store_true",
        help="disable the tqdm progress bar display",
    )

    # Default tag values used for uniquely identifying the DICOM series:
    # Based on GDCM::SerieHelper::CreateDefaultUniqueSeriesIdentifier
    # https://github.com/malaterre/GDCM/blob/c10068ff26e7a6905fa9b75d9f45a7c4ce9d5591/Source/MediaStorageAndFileFormat/gdcmSerieHelper.cxx#L72C6-L99
    # 0020|000e - series instance UID
    # 0020|000d - study Instance UID
    # 0020|0011 - series number
    # 0018|0024 - sequence name
    # 0018|0050 - slice thickness
    # 0028|0010 - rows
    # 0028|0011 - columns
    opt_arg_parser.add_argument(
        "--additional_series_tags",
        default=[
            "0020|0011",
            "0018|0024",
            "0018|0050",
            "0028|0010",
            "0028|0011",
        ],
        nargs="+",
        help="tags used to uniquely identify image files that "
        "belong to the same DICOM series, these are in addition to 0020|000e, series instance UID, and 0020|000d, study Instance UID",
    )
    # query SimpleITK for the list of registered ImageIO types
    opt_arg_parser.add_argument(
        "--imageIO",
        default="All",
        choices=list(sitk.ImageFileReader().GetRegisteredImageIOs()) + ["All"],
        help="SimpleITK imageIO to use for reading (e.g. BMPImageIO)",
    )
    opt_arg_parser.add_argument(
        "--external_applications",
        default=[],
        nargs="*",
        help="paths to external applications",
    )
    opt_arg_parser.add_argument(
        "--external_applications_headings",
        default=[],
        nargs="*",
        help="titles of the results columns for external applications",
    )
    opt_arg_parser.add_argument(
        "--metadata_keys",
        nargs="*",
        default=[],
        help="inspect values of these metadata keys (DICOM tags or other keys stored in the file)",
    )
    opt_arg_parser.add_argument(
        "--metadata_keys_headings",
        default=[],
        nargs="*",
        help="titles of the results columns for the metadata_keys",
    )
    opt_arg_parser.add_argument(
        "--ignore_problems",
        action="store_true",
        help="problematic files/series will not be listed if parameter is given on commandline",
    )
    opt_arg_parser.add_argument(
        "--create_summary_image",
        action="store_true",
        help="create a summary image, volume of thumbnails representing all images",
    )
    opt_arg_parser.add_argument(
        "--thumbnail_sizes",
        type=positive_int,
        nargs=2,
        default=[64, 64],
        help="size of thumbnail images used to create summary image",
    )
    opt_arg_parser.add_argument(
        "--tile_sizes",
        type=positive_int,
        nargs=2,
        default=[20, 20],
        help="number of thumbnail images used to create single tile in summary image",
    )
    opt_arg_parser.add_argument(
        "--projection_axis",
        type=int,
        choices=[0, 1, 2],
        default=2,
        help="for 3D images, perform maximum intensity projection along this axis",
    )
    opt_arg_parser.add_argument(
        "--interpolator",
        choices=["sitkNearestNeighbor", "sitkLinear", "sitkBSpline3"],
        default="sitkNearestNeighbor",
        help="SimpleITK interpolator used to resize images when creating summary image",
    )
    # Use the function docstring as the text in the parser description and a custom
    # RawDescriptionAndDefaultHelpFormatter so that the docstring layout
    # is maintained, otherwise it is line-wrapped and the formatting is lost, and the
    # default values for optional parameters are displayed with the help message.
    parser = argparse.ArgumentParser(
        description=characterize_data.__doc__,
        formatter_class=RawDescriptionAndDefaultHelpFormatter,
        parents=[opt_arg_parser],
    )
    parser.add_argument(
        "root_of_data_directory",
        type=dir_path,
        help="path to the topmost directory containing data",
    )
    parser.add_argument("output_file", type=file_path, help="output csv file path")
    parser.add_argument(
        "analysis_type",
        choices=["per_file", "per_series"],
        default="per_file",
        help='type of analysis, "per_file" or "per_series"',
    )

    args = parser.parse_args(argv)
    if args.configuration_file:
        new_default_settings = load_optional_parameters(
            args.configuration_file, opt_arg_parser
        )
        # Configuration file overrides the hard coded default settings
        # which are then overridden by the commandline settings by
        # calling the parse_args again.
        parser.set_defaults(**new_default_settings)
        args = parser.parse_args(argv)

    # keep a copy of the original settings before some are converted to
    # internal representations.
    save_dict = copy.deepcopy(vars(args))
    # Convert some entries from string representation to corresponding SimpleITK values
    if args.imageIO == "All":
        args.imageIO = ""
    # The original args.inerpolator valued is guaranteed to be valid because of the use of
    # choices in the argument parser.
    args.interpolator = getattr(sitk, args.interpolator)

    # Enforce constraints not enforced by the argparse argument types.
    if len(args.external_applications) != len(args.external_applications_headings):
        print(
            "Number of external applications and their headings do not match.",
            file=sys.stderr,
        )
        return 1
    if len(args.metadata_keys) != len(args.metadata_keys_headings):
        print(
            "Number of metadata keys and their headings do not match.", file=sys.stderr
        )
        return 1

    thumbnail_settings = {}
    if args.create_summary_image:
        thumbnail_settings["thumbnail_sizes"] = args.thumbnail_sizes
        thumbnail_settings["projection_axis"] = args.projection_axis
        thumbnail_settings["interpolator"] = args.interpolator
    if args.analysis_type == "per_file":
        df = inspect_files(
            args.root_of_data_directory,
            args.max_processes,
            args.disable_tqdm,
            imageIO=args.imageIO,
            meta_data_info=dict(zip(args.metadata_keys_headings, args.metadata_keys)),
            external_programs_info=dict(
                zip(args.external_applications_headings, args.external_applications)
            ),
            thumbnail_settings=thumbnail_settings,
        )
    elif args.analysis_type == "per_series":
        df = inspect_series(
            args.root_of_data_directory,
            args.max_processes,
            args.disable_tqdm,
            # series and study instance UIDs are always included as series_tags used
            # to aggregate files belonging to the same series, no matter what the user
            # specifies. Use set to ensure no duplicates in user input and convert all
            # to lowercase as these strings represent hexadecimal numbers, so 0020|000E
            # and 0020|000e are equivalent.
            additional_series_tags=list(
                set([t.lower() for t in args.additional_series_tags])
                - {"0020|000e", "0020|000d"}
            ),
            meta_data_info=dict(zip(args.metadata_keys_headings, args.metadata_keys)),
            thumbnail_settings=thumbnail_settings,
        )
    # either no files were found in the root directory structure or no images could be read,
    # so dataframe is either empty or has a single column titled "files" and all the contents
    # are just listing files/series that could not be read.
    if len(df) == 0 or len(df.columns) == 1:
        print(
            f"No report created, no successfully read images from root directory ({args.root_of_data_directory})"
        )
        return 0

    # Create output directory if needed
    dirname = os.path.dirname(args.output_file)
    if not dirname:
        dirname = "."
    os.makedirs(dirname, exist_ok=True)

    # Save the configuration used in the analysis to a JSON configuration file
    # with date-time prefix. The positional parameters and configuration file
    # are not included. Enables reproducibility and consistent usage of user
    # preferences across script invocations.
    with open(
        os.path.join(
            dirname,  # os.path.dirname(os.path.abspath(__file__)),
            time.strftime("%d_%m_%Y-%H_%M_%S_") + "characterize_data_settings.json",
        ),
        "w",
    ) as fp:
        del save_dict["configuration_file"]
        del save_dict["root_of_data_directory"]
        del save_dict["output_file"]
        del save_dict["analysis_type"]
        json.dump(save_dict, fp, indent=2)

    # create summary image and remove the column containing the thumbnail images from the
    # dataframe.
    if args.create_summary_image:
        faux_volume = image_list_to_faux_volume(
            df["thumbnail"].dropna().to_list(), args.tile_sizes
        )
        sitk.WriteImage(
            faux_volume,
            f"{os.path.splitext(args.output_file)[0]}_summary_image.nrrd",
            useCompression=True,
        )
        df.drop("thumbnail", axis=1, inplace=True)

    # remove all rows associated with problematic files (non-image files or image files with problems).
    # all the valid rows contain at least 2 non-na values so use that threshold when dropping rows.
    if args.ignore_problems:
        df.dropna(inplace=True, thresh=2)
    # save the raw information, create directory structure if it doesn't exist
    df.to_csv(args.output_file, index=False)

    # minimal analysis on the image information, detect image duplicates and plot the image size,
    # spacing and min/max intensity values of scalar image distributions as scatterplots.
    # first drop the rows that correspond to problematic files if they weren't already dropped
    # based on program settings
    if not args.ignore_problems:
        df.dropna(inplace=True, thresh=2)
    image_counts = df["MD5 intensity hash"].value_counts().reset_index(name="count")
    duplicates = df[
        df["MD5 intensity hash"].isin(
            image_counts[image_counts["count"] > 1]["MD5 intensity hash"]
        )
    ].sort_values(by=["MD5 intensity hash"])
    if not duplicates.empty:
        duplicates.to_csv(
            f"{os.path.splitext(args.output_file)[0]}_duplicates.csv", index=False
        )

    size_fig, size_ax = plt.subplots()
    spacing_fig, spacing_ax = plt.subplots()
    # There are true 3D images in the dataset, convert 2D sizes
    # to faux 3D ones by adding third dimension as 1 and treat all
    # images as 3D. Plot as a scatterplot with x and y sizes axes
    # and z size encoded via color.
    if df["image size"].apply(lambda x: len(x) == 3 and x[2] > 1).any():
        sizes = df["image size"].apply(lambda x: x if len(x) == 3 else x + (1,))
        x_size, y_size, z_size = zip(*sizes)
        sc = size_ax.scatter(x_size, y_size, c=z_size, cmap="viridis")
        cb = size_fig.colorbar(sc)
        cb.set_label("z size", rotation=270, verticalalignment="baseline")
        cb.set_ticks(np.linspace(min(z_size), max(z_size), 5, endpoint=True, dtype=int))

        spacings = df["image spacing"].apply(lambda x: x if len(x) == 3 else x + (1,))
        x_spacing, y_spacing, z_spacing = zip(*spacings)
        sc = spacing_ax.scatter(x_spacing, y_spacing, c=z_spacing, cmap="viridis")
        cb = spacing_fig.colorbar(sc)
        cb.set_label("z spacing [mm]", rotation=270, verticalalignment="baseline")

    # All images are 2D, but some may be faux 3D, last dimension is 1,
    # convert faux 3D sizes to 2D by removing the last dimension.
    else:
        sizes = df["image size"].apply(lambda x: x if len(x) == 2 else x[0:2])
        x_size, y_size = zip(*sizes)
        size_ax.scatter(x_size, y_size)

        spacings = df["image spacing"].apply(lambda x: x if len(x) == 2 else x[0:2])
        x_spacing, y_spacing = zip(*spacings)
        spacing_ax.scatter(x_spacing, y_spacing)

    size_ax.set_xlabel("x size")
    size_ax.set_ylabel("y size")
    size_fig.tight_layout()
    size_fig.savefig(
        f"{os.path.splitext(args.output_file)[0]}_image_size_scatterplot.pdf",
        bbox_inches="tight",
    )
    spacing_ax.set_xlabel("x spacing [mm]")
    spacing_ax.set_ylabel("y spacing [mm]")
    spacing_fig.tight_layout()
    spacing_fig.savefig(
        f"{os.path.splitext(args.output_file)[0]}_image_spacing_scatterplot.pdf",
        bbox_inches="tight",
    )

    # there is at least one series/file that is grayscale
    if "min intensity" in df.columns:
        min_intensities = df["min intensity"].dropna()
        max_intensities = df["max intensity"].dropna()
        if not min_intensities.empty:
            fig, ax = plt.subplots()
            ax.scatter(min_intensities, max_intensities)
            ax.set_xlabel("min intensity")
            ax.set_ylabel("max intensity")
            fig.savefig(
                f"{os.path.splitext(args.output_file)[0]}_min_max_intensity_scatterplot.pdf",
                bbox_inches="tight",
            )

    return 0


if __name__ == "__main__":
    sys.exit(characterize_data())
