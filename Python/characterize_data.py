import SimpleITK as sitk
import pandas as pd
import numpy as np
import os
import sys
import shutil
import subprocess
import platform
import matplotlib.pyplot as plt

# We use the multiprocess package instead of the official
# multiprocessing as it currently has several issues as discussed
# on the software carpentry page: https://hpc-carpentry.github.io/hpc-python/06-parallel/
import multiprocess as mp
from functools import partial
import argparse

import hashlib
import tempfile

# Maximal number of parallel processes we run.
MAX_PROCESSES = 15

"""
This script inspects/characterizes images in a given directory structure. It
recursively traverses the directories and either inspects the files one by one
or if in DICOM series inspection mode, inspects the data on a per series basis
(all 2D series files combined into a single 3D image).

To run the script one needs to specify:
    1. Root of the data directory.
    2. Output file name.
    3. The analysis type to perform per_file or per_series. The latter indicates
       we are only interested in DICOM files. When run using per_file empty lines
       in the results file are due to:
           a. The file is not an image or is a corrupt image file.
           b. SimpleITK was unable to read the image file (contact us with an example).
    4. Optional SimpleITK imageIO to use. The default value is
       the empty string, indicating that all file types should be read.
       To see the set of ImageIO types supported by your version of SimpleITK,
       call ImageFileReader::GetRegisteredImageIOs() or simply print an
       ImageFileReader object.
    5. Optional external applications to run. Their return value (zero or
       non zero) is used to log success or failure. A nice example is the
       dciodvfy program from David Clunie (https://www.dclunie.com/dicom3tools.html)
       which validates compliance with the DICOM standard.
    6. When the external applications are provided corresponding column headings
       are also required. These are used in the output csv file.
    7. Optional metadata keys. These are image specific keys such as DICOM tags
       or other metadata tags that may be found in the image. The content of the
       tags is written to the result file.
    8. When the metadata tags are provided corresponding column headings
       are also required. These are used in the output csv file.

Examples:
Run a generic file analysis:
python characterize_data.py ../Data/ Output/generic_image_data_report.csv per_file \
--imageIO "" --external_applications ./dciodvfy --external_applications_headings "DICOM Compliant" \
--metadata_keys "0008|0060" "0018|5101" --metadata_keys_headings "modality" "radiographic view"


Run a DICOM series based analysis:
python characterize_data.py ../Data/ Output/DICOM_image_data_report.csv per_series \
--metadata_keys "0008|0060" "0018|5101" --metadata_keys_headings "modality" "radiographic view"

Output:
The raw information is written to the specified output file (e.g. output.csv).
Additionally, minimal analysis of the raw information is performed:
1. If there are duplicate images these are reported in output_duplicates.csv.
2. Two figures: output_image_size_distribution.pdf and output_min_max_intensity_distribution.pdf
"""


def inspect_image(sitk_image, image_info, current_index, meta_data_keys=[]):
    """
    Inspect a SimpleITK image, return a list of parameters characterizing the image.

    Parameters
    ----------
    sitk_image (SimpleITK.Image): Input image for inspection.
    image_info (list): Image information is written to this list, starting at current_index.
                       [,,,MD5 intensity hash,
                        image size, image spacing, image origin, axis direction,
                        pixel type, min intensity, max intensity,
                        meta data_1...meta_data_n,,,]
    current_index (int): Starting index into the image_info list.
    meta_data_keys(list(str)): The image's meta-data dictionary keys whose value we want to
                               inspect.
    Returns
    -------
    index to the next empty entry in the image_info list.
    The image_info list is filled with the following values:
    MD5 intensity hash - Enable identification of duplicate images in terms of intensity.
                         This is different from SimpleITK image equality where the
                         same intensities with different image spacing/origin/direction cosine
                         are considered different images as they occupy a different spatial
                         region.
    image size - number of pixels in each dimension.
    pixel type - type of pixels (scalar - gray, vector - gray or color).
    min/max intensity - if a scalar image, min and max values.
    meta data_i - value of image's metadata dictionary for given key (e.g. .
    """
    image_info[current_index] = hashlib.md5(
        sitk.GetArrayViewFromImage(sitk_image)
    ).hexdigest()
    current_index = current_index + 1
    image_info[current_index] = sitk_image.GetSize()
    current_index = current_index + 1
    image_info[current_index] = sitk_image.GetSpacing()
    current_index = current_index + 1
    image_info[current_index] = sitk_image.GetOrigin()
    current_index = current_index + 1
    image_info[current_index] = sitk_image.GetDirection()
    current_index = current_index + 1
    if (
        sitk_image.GetNumberOfComponentsPerPixel() == 1
    ):  # greyscale image, get the min/max pixel values
        image_info[current_index] = sitk_image.GetPixelIDTypeAsString() + " gray"
        current_index = current_index + 1
        mmfilter = sitk.MinimumMaximumImageFilter()
        mmfilter.Execute(sitk_image)
        image_info[current_index] = mmfilter.GetMinimum()
        current_index = current_index + 1
        image_info[current_index] = mmfilter.GetMaximum()
        current_index = current_index + 1
    else:  # either a color image or a greyscale image masquerading as a color one
        pixel_type = sitk_image.GetPixelIDTypeAsString()
        channels = [
            sitk.GetArrayFromImage(sitk.VectorIndexSelectionCast(sitk_image, i))
            for i in range(sitk_image.GetNumberOfComponentsPerPixel())
        ]
        if np.array_equal(channels[0], channels[1]) and np.array_equal(
            channels[0], channels[2]
        ):
            pixel_type = (
                pixel_type
                + f" {sitk_image.GetNumberOfComponentsPerPixel()} channels gray"
            )
        else:
            pixel_type = (
                pixel_type
                + f" {sitk_image.GetNumberOfComponentsPerPixel()} channels color"
            )
        image_info[current_index] = pixel_type
        current_index = current_index + 3
    img_keys = sitk_image.GetMetaDataKeys()
    for k in meta_data_keys:
        if k in img_keys:
            image_info[current_index] = sitk_image.GetMetaData(k)
        current_index = current_index + 1
    return current_index


def inspect_single_file(file_name, imageIO="", meta_data_keys=[], external_programs=[]):
    """
    Inspect a file using the specified imageIO, returning a list with the relevant information.

    Parameters
    ----------
    file_name (str): Image file name.
    imageIO (str): Name of image IO to use. To see the list of registered image IOs use the
                   ImageFileReader::GetRegisteredImageIOs() or print an ImageFileReader.
                   The empty string indicates to read all file formats supported by SimpleITK.
    meta_data_keys(list(str)): The image's meta-data dictionary keys whose value we want to
                               inspect.
    external_programs(list(str)): A list of programs we will run with the file_name as input
                                  the return value 'succeeded' or 'failed' is recorded. This is useful
                                  for example if you need to validate conformance to a standard
                                  such as DICOM.

    Returns
    -------
     list with the following entries: [file name, MD5 intensity hash,
                                       image size, image spacing, image origin, axis direction,
                                       pixel type, min intensity, max intensity,
                                       meta data_1...meta_data_n,
                                       external_program_res_1...external_program_res_m]
    If the given file is not readable by SimpleITK, the only meaningful entry in the list
    will be the file name (all other values will be either None or NaN).
    """
    file_info = [None] * (9 + len(meta_data_keys) + len(external_programs))
    file_info[0] = file_name
    current_index = 1
    try:
        reader = sitk.ImageFileReader()
        reader.SetImageIO(imageIO)
        reader.SetFileName(file_name)
        img = reader.Execute()
        current_index = inspect_image(img, file_info, current_index, meta_data_keys)
        for p in external_programs:
            try:
                # run the external programs, check the return value, and capture all output so it
                # doesn't appear on screen. The CalledProcessError exception is raised if the
                # external program fails (returns non zero value).
                subprocess.run([p, file_name], check=True, capture_output=True)
                file_info[current_index] = "succeeded"
            except Exception:
                file_info[current_index] = "failed"
            current_index = current_index + 1
    except Exception:
        pass
    return file_info


def inspect_files(
    root_dir,
    imageIO="",
    meta_data_keys=[],
    external_programs=[],
    additional_column_names=[],
):
    """
    Iterate over a directory structure and return a pandas dataframe with the relevant information for the
    image files. This also includes non image files. The resulting dataframe will only include the file name
    if that file wasn't successfully read by SimpleITK. The two reasons for failure are: (1) the user specified
    imageIO isn't compatible with the file format (user is only interested in reading jpg and the file
    format is mha) or (2) the file could not be read by the SimpleITK IO (corrupt file or unexpected limitation of
    SimpleITK).

    Parameters
    ----------
    root_dir (str): Path to the root of the data directory. Traverse the directory structure
                    and inspect every file (also report non image files, in which
                    case the only valid entry will be the file name).
    imageIO (str): Name of image IO to use. To see the list of registered image IOs use the
                   ImageFileReader::GetRegisteredImageIOs() or print an ImageFileReader.
                   The empty string indicates to read all file formats supported by SimpleITK.
    meta_data_keys(list(str)): The image's meta-data dictionary keys whose value we want to
                               inspect.
    external_programs(list(str)): A list of programs we will run with the file_name as input
                                  the return value 'succeeded' or 'failed' is recorded. This
                                  is useful for example if you need to validate conformance
                                  to a standard such as DICOM.
    additional_column_names (list(str)): Column names corresponding to the contents of the
                                         meta_data_keys and external_programs lists.
    Returns
    -------
    pandas DataFrame: Each row in the data frame corresponds to a single file.

    """
    if len(meta_data_keys) + len(external_programs) != len(additional_column_names):
        raise ValueError("Number of additional column names does not match expected.")
    column_names = [
        "file name",
        "MD5 intensity hash",
        "image size",
        "image spacing",
        "image origin",
        "axis direction",
        "pixel type",
        "min intensity",
        "max intensity",
    ] + additional_column_names
    all_file_names = []
    for dir_name, subdir_names, file_names in os.walk(root_dir):
        all_file_names += [
            os.path.join(os.path.abspath(dir_name), fname) for fname in file_names
        ]
    # Get list of lists describing the results and then combine into a dataframe, faster
    # than appending to the dataframe one by one. Use parallel processing to speed things up.
    if platform.system() == "Windows":
        res = map(
            partial(
                inspect_single_file,
                imageIO=imageIO,
                meta_data_keys=meta_data_keys,
                external_programs=external_programs,
            ),
            all_file_names,
        )
    else:
        with mp.Pool(processes=MAX_PROCESSES) as pool:
            res = pool.map(
                partial(
                    inspect_single_file,
                    imageIO=imageIO,
                    meta_data_keys=meta_data_keys,
                    external_programs=external_programs,
                ),
                all_file_names,
            )
    return pd.DataFrame(res, columns=column_names)


def inspect_single_series(series_data, meta_data_keys=[]):
    """
    Inspect a single DICOM series (DICOM hierarchy of patient-study-series-image).
    This can be a single file, or multiple files such as a CT or
    MR volume.

    Parameters
    ----------
    series_data (two entry tuple): First entry is study:series, second entry is the list of
                                   files comprising this series.
    meta_data_keys(list(str)): The image's meta-data dictionary keys whose value we want to
                               inspect.
    Returns
    -------
     list with the following entries: [study:series, MD5 intensity hash,
                                       image size, image spacing, image origin, axis direction,
                                       pixel type, min intensity, max intensity,
                                       meta data_1...meta_data_n]
    """
    series_info = [None] * (9 + len(meta_data_keys))
    series_info[0] = series_data[1]
    current_index = 1
    try:
        reader = sitk.ImageSeriesReader()
        reader.MetaDataDictionaryArrayUpdateOn()
        reader.LoadPrivateTagsOn()
        _, sid = series_data[0].split(":")
        file_names = series_data[1]
        # As the files comprising a series with multiple files can reside in
        # separate directories and SimpleITK expects them to be in a single directory
        # we use a tempdir and symbolic links to enable SimpleITK to read the series as
        # a single image. Additionally the files are renamed as they may have resided in
        # separate directories with the same file name. Finally, unfortunately on Windows
        # we copy the files to the tempdir as the os.symlink documentation says that
        # "On newer versions of Windows 10, unprivileged accounts can create symlinks
        # if Developer Mode is enabled. When Developer Mode is not available/enabled,
        # the SeCreateSymbolicLinkPrivilege privilege is required, or the process must be
        # run as an administrator."
        with tempfile.TemporaryDirectory() as tmpdirname:
            if platform.system() == "Windows":
                for i, fname in enumerate(file_names):
                    shutil.copy(
                        os.path.abspath(fname), os.path.join(tmpdirname, str(i))
                    )
            else:
                for i, fname in enumerate(file_names):
                    os.symlink(os.path.abspath(fname), os.path.join(tmpdirname, str(i)))
            reader.SetFileNames(
                sitk.ImageSeriesReader_GetGDCMSeriesFileNames(tmpdirname, sid)
            )
            img = reader.Execute()
            for k in meta_data_keys:
                if reader.HasMetaDataKey(0, k):
                    img.SetMetaData(k, reader.GetMetaData(0, k))
            inspect_image(img, series_info, current_index, meta_data_keys)
    except Exception:
        pass
    return series_info


def inspect_series(root_dir, meta_data_keys=[], additional_column_names=[]):
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
    meta_data_keys(list(str)): The series meta-data dictionary keys whose value we want to
                               inspect.
    additional_column_names (list(str)): Column names corresponding to the contents of the
                                         meta_data_keys list.
    Returns
    -------
    pandas DataFrame: Each row in the data frame corresponds to a single file.
    """
    if len(meta_data_keys) != len(additional_column_names):
        raise ValueError("Number of additional column names does not match expected.")
    column_names = [
        "files",
        "MD5 intensity hash",
        "image size",
        "image spacing",
        "image origin",
        "axis direction",
        "pixel type",
        "min intensity",
        "max intensity",
    ] + additional_column_names
    all_series_files = {}
    reader = sitk.ImageFileReader()
    # collect the file names of all series into a dictionary with the key being
    # study:series. This traversal is faster, O(n), than calling GetGDCMSeriesIDs on each
    # directory followed by iterating over the series and calling
    # GetGDCMSeriesFileNames with the seriesID on that directory, O(n^2).
    for dir_name, subdir_names, file_names in os.walk(root_dir):
        for file in file_names:
            try:
                fname = os.path.join(dir_name, file)
                reader.SetFileName(fname)
                reader.ReadImageInformation()
                sid = reader.GetMetaData("0020|000e")
                study = reader.GetMetaData("0020|000d")
                key = f"{study}:{sid}"
                if key in all_series_files:
                    all_series_files[key].append(fname)
                else:
                    all_series_files[key] = [fname]
            except Exception:
                pass
    # Get list of lists describing the results and then combine into a dataframe, faster
    # than appending to the dataframe one by one.
    res = [
        inspect_single_series(series_data, meta_data_keys)
        for series_data in all_series_files.items()
    ]
    return pd.DataFrame(res, columns=column_names)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "root_of_data_directory", help="path to the topmost directory containing data"
    )
    parser.add_argument("output_file", help="output csv file path")
    parser.add_argument(
        "analysis_type",
        default="per_file",
        help='type of analysis, "per_file" or "per_series"',
    )
    parser.add_argument(
        "--imageIO",
        default="",
        help="SimpleITK imageIO to use for reading (e.g. BMPImageIO)",
    )
    parser.add_argument(
        "--external_applications",
        default=[],
        nargs="*",
        help="paths to external applications",
    )
    parser.add_argument(
        "--external_applications_headings",
        default=[],
        nargs="*",
        help="titles of the results columns for external applications",
    )
    parser.add_argument(
        "--metadata_keys",
        nargs="*",
        default=[],
        help="inspect values of these metadata keys (DICOM tags or other keys stored in the file)",
    )
    parser.add_argument(
        "--metadata_keys_headings",
        default=[],
        nargs="*",
        help="titles of the results columns for the metadata_keys",
    )

    args = parser.parse_args(argv)
    if len(args.external_applications) != len(args.external_applications_headings):
        print("Number of external applications and their headings do not match.")
        sys.exit(1)
    if len(args.metadata_keys) != len(args.metadata_keys_headings):
        print("Number of metadata keys and their headings do not match.")
        sys.exit(1)
    if args.analysis_type not in ["per_file", "per_series"]:
        print("Unexpected analysis type.")
        sys.exit(1)

    if args.analysis_type == "per_file":
        df = inspect_files(
            args.root_of_data_directory,
            imageIO=args.imageIO,
            meta_data_keys=args.metadata_keys,
            external_programs=args.external_applications,
            additional_column_names=args.metadata_keys_headings
            + args.external_applications_headings,
        )
    elif args.analysis_type == "per_series":
        df = inspect_series(
            args.root_of_data_directory,
            meta_data_keys=args.metadata_keys,
            additional_column_names=args.metadata_keys_headings,
        )
    # save the raw information, create directory structure if it doesn't exist
    os.makedirs(os.path.dirname(args.output_file), exist_ok=True)
    df.to_csv(args.output_file, index=False)

    # minimal analysis on the image information, detect image duplicates and plot the image size
    # distribution and distribution of min/max intensity values of scalar
    # images
    image_counts = (
        df["MD5 intensity hash"].dropna().value_counts().reset_index(name="count")
    )
    duplicates = df[
        df["MD5 intensity hash"].isin(image_counts[image_counts["count"] > 1]["index"])
    ].sort_values(by=["MD5 intensity hash"])
    if not duplicates.empty:
        duplicates.to_csv(
            f"{os.path.splitext(args.output_file)[0]}_duplicates.csv", index=False
        )

    size_counts = (
        df["image size"]
        .astype("string")
        .dropna()
        .value_counts()
        .reset_index(name="count")
    )
    if not size_counts.empty:
        # Compute appropriate size for figure using a specific font size
        # based on stack-overflow: https://stackoverflow.com/questions/35127920/overlapping-yticklabels-is-it-possible-to-control-cell-size-of-heatmap-in-seabo
        fontsize_pt = 8
        dpi = 72.27

        # compute the matrix height in points and inches
        matrix_height_pt = fontsize_pt * len(size_counts)
        matrix_height_in = matrix_height_pt / dpi

        # compute the required figure height
        top_margin = 0.04  # in percentage of the figure height
        bottom_margin = 0.04  # in percentage of the figure height
        figure_height = matrix_height_in / (1 - top_margin - bottom_margin)

        # build the figure instance with the desired height
        fig, ax = plt.subplots(
            figsize=(6, figure_height),
            gridspec_kw=dict(top=1 - top_margin, bottom=bottom_margin),
        )

        ax.tick_params(axis="y", labelsize=fontsize_pt)
        ax.tick_params(axis="x", labelsize=fontsize_pt)
        ax.xaxis.get_major_locator().set_params(integer=True)
        ax = size_counts.plot.barh(
            x="index",
            y="count",
            xlabel="image size",
            ylabel="# of images",
            legend=None,
            ax=ax,
        )
        ax.bar_label(
            ax.containers[0], fontsize=fontsize_pt
        )  # add the number at the top of each bar
        plt.savefig(
            f"{os.path.splitext(args.output_file)[0]}_image_size_distribution.pdf",
            bbox_inches="tight",
        )

    min_intensities = df["min intensity"].dropna()
    max_intensities = df["max intensity"].dropna()
    if not min_intensities.empty:
        fig, ax = plt.subplots()
        ax.yaxis.get_major_locator().set_params(integer=True)
        ax.hist(
            min_intensities,
            bins=256,
            alpha=0.5,
            label="min intensity",
            color="blue",
        )
        ax.hist(
            max_intensities,
            bins=256,
            alpha=0.5,
            label="max intensity",
            color="green",
        )
        plt.legend()
        plt.xlabel("intensity")
        plt.ylabel("# of images")
        plt.savefig(
            f"{os.path.splitext(args.output_file)[0]}_min_max_intensity_distribution.pdf",
            bbox_inches="tight",
        )

    sys.exit(0)


if __name__ == "__main__":
    sys.exit(main())
