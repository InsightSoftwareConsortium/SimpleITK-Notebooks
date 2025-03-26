import os

import pytest
import pathlib
import hashlib
import sys
import pandas as pd

# Add the script source directory to the path so that we can import
sys.path.append(str(pathlib.Path(__file__).parent.parent.absolute() / "Python/scripts"))

from characterize_data import characterize_data


class TestScripts:
    def setup_method(self):
        # Path to testing data is expected in the following location:
        self.data_path = pathlib.Path(__file__).parent.parent.absolute() / "Data"

    def files_md5(self, ascii_file_list, binary_file_list):
        """
        Compute a single/combined md5 hash for a list of ascii and binary files.
        We can't read all files as binary because of platform specific differences in
        ascii files. For ascii files we need to open in text mode and use the read() method which
        to quote the documentation:
        In text mode, the default when reading is to convert platform-specific line endings (\n on Unix, \r\n on
        Windows) to just \n.

        This ensures that we get the same md5 hash on all platforms. If we opened the text files as binary the hashes
        become platform dependent (\r\n vs. \n).
        """
        md5 = hashlib.md5()
        for file_name in ascii_file_list:
            with open(file_name, "r") as fp:
                file_contents = fp.read()
                md5.update(file_contents.encode("utf-8"))
        for file_name in binary_file_list:
            with open(file_name, "rb") as fp:
                file_contents = fp.read()
                md5.update(file_contents)
        return md5.hexdigest()

    @pytest.mark.parametrize(
        "output_file, analysis_type, user_configuration, result_md5hash",
        [
            (
                "per_file_data_characteristics.csv",
                "per_file",
                "characterize_data_user_defaults.json",
                "fb0338866794ef68c5d5854399ccd22c",
            ),
            (
                "per_series_data_characteristics.csv",
                "per_series",
                "characterize_data_user_defaults.json",
                "766184c8503a2f08cac6e3b6be57e346",
            ),
        ],
    )
    def test_characterize_data(
        self, output_file, analysis_type, user_configuration, result_md5hash, tmp_path
    ):
        # NOTE: For now not testing pdf files. Setting the SOURCE_DATE_EPOCH
        # didn't resolve the variability across platforms, getting different
        # md5 hash values. Not sure if it is possible to do regression testing
        # with the pdf files.
        # Set the SOURCE_DATE_EPOCH environment variable value so that the pdf,ps files
        # created have the same date. The file content includes the date time and we want
        # to ignore that difference.
        # https://github.com/matplotlib/matplotlib/issues/6317/
        # os.environ["SOURCE_DATE_EPOCH"] = "42"
        output_dir = tmp_path
        # Run the script, output files are written to the output_path directory
        # these are csv and pdf files
        characterize_data(
            [
                str(self.data_path / "CIRS057A_MR_CT_DICOM"),
                str(output_dir / output_file),
                analysis_type,
                "--configuration_file",
                str(self.data_path / user_configuration),
            ]
        )
        # csv files needs to be modified as follows before comparing to expected values:
        # 1. Modify absolute file paths to only include file name so that they are independent
        #    of file location.
        # 2. Sort the file names in the "files" column, os.walk returns directories and file
        #    names in arbitrary order and the order is different across operating systems.
        # 3. Sort the image entries (per series or per file) according to MD5 hash as the row order
        #    depends on the directory order which isn't consistent, same issue as in 2.
        result_files = output_dir.glob("*.csv")
        for file in result_files:
            df = pd.read_csv(file).sort_values(by="MD5 intensity hash")
            df["files"] = df["files"].apply(
                lambda x: sorted([pathlib.Path(fname).name for fname in eval(x)])
            )
            df.to_csv(file, index=False)
        # Below we convert the generators to lists and concatenate them. A nicer way of
        # concatenating iterables with a large number of entries is to use itertools.chain().
        # In our case, the number of entries is small (<5) and we don't want to add the dependency
        # on the itertools package, so just convert to list.
        assert (
            self.files_md5(
                ascii_file_list=list(output_dir.glob("*.csv"))
                + list(output_dir.glob("*.json")),
                binary_file_list=[],  # output_dir.glob("*.pdf"),
            )
            == result_md5hash
        )
