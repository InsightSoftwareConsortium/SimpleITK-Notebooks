import os
import subprocess
import tempfile

import nbformat
import pytest

"""
run all tests:
pytest -v --tb=short

run specific test:
pytest -v --tb=short tests/test_notebooks.py::Test_notebooks::test_10_matplotlibs_imshow

-s : disable all capturing of output.
-m marker_name: run only tests marked with 'marker_name' (python_notebook, r_notebook). 

-m logical_expression: run only tests for which the logical expression is true such as 
                       "python_notebook and not large_memory"

"""

class Test_notebooks_py2(object):
    """
    Testing of SimpleITK Jupyter notebooks:
    1. Check that notebooks do not contain output (sanity check as these should 
       not have been pushed to the repository).
    2. Run the notebook and check for errors. In some notebooks we 
       intentionally cause errors to illustrate certain features of the toolkit. 
       All code cells that intentionally generate an error are expected to be 
       marked using the cell's metadata. In the notebook go to 
       "View->Cell Toolbar->Edit Metadata and add the following json: 
       
       "simpleitk_error_expected": simpleitk_error_message

       Cells where an error is allowed, but not necessarily expected should be marked
       with the following json:

       "simpleitk_error_allowed": simpleitk_error_message

       The simpleitk_error_message is a substring of the generated error
       message, such as 'Exception thrown in SimpleITK Show:'
    """
    def evaluate_notebook(self, path, kernel_name):
        """
        Execute a notebook via nbconvert and print the results of the test (errors etc.)
        Args:
            path (string): Name of notebook to run.
            kernel_name (string): Which jupyter kernel to use to run the test. 
                                  Relevant values are:'python2', 'python3', 'ir'.
        """
        allowed_error_markup = 'simpleitk_error_allowed'
        expected_error_markup = 'simpleitk_error_expected'

        dir_name, file_name = os.path.split(path)
        if dir_name:
            os.chdir(dir_name)

        print('-------- begin (kernel {0}) {1} --------'.format(kernel_name,file_name))
        
        # Check that the notebook does not contain output from code cells 
        # (should not be in the repository, but well...).
        nb = nbformat.read(path, nbformat.current_nbformat)
        no_unexpected_output = True
        # Check that the cell dictionary has an 'outputs' key and that it is empty, relies
        # on Python using short circuit evaluation so that we don't get KeyError when retrieving
        # the 'outputs' entry.
        cells_with_output = [c.source for c in nb.cells if 'outputs' in c and c.outputs]
        if cells_with_output:
            no_unexpected_output = False
            print('Cells with unexpected output:')
            for cell in cells_with_output: 
                print(cell+'\n---')


        # Execute the notebook and allow errors (run all cells), output is
        # written to a temporary file which is automatically deleted.
        with tempfile.NamedTemporaryFile(suffix='.ipynb') as fout:
            args = ['jupyter', 'nbconvert', 
                    '--to', 'notebook', 
                    '--execute',
                    '--ExecutePreprocessor.kernel_name='+kernel_name, 
                    '--ExecutePreprocessor.allow_errors=True',
                    '--ExecutePreprocessor.timeout=600', # seconds till timeout 
                    '--output', fout.name, path]
            subprocess.check_call(args)
            nb = nbformat.read(fout.name, nbformat.current_nbformat)

        # Get all of the unexpected errors (logic: cell has output with an error
        # and no error is expected or the allowed/expected error is not the one which
        # was generated.)
        unexpected_errors = [(output.evalue, c.source) for c in nb.cells \
                              if 'outputs' in c for output in c.outputs \
                              if (output.output_type=='error') and \
                               (((allowed_error_markup not in c.metadata) and (expected_error_markup not in c.metadata))or \
                               ((allowed_error_markup in c.metadata) and (c.metadata[allowed_error_markup] not in output.evalue)) or \
                               ((expected_error_markup in c.metadata) and (c.metadata[expected_error_markup] not in output.evalue)))]
        
        no_unexpected_errors = True 
        if unexpected_errors:
            no_unexpected_errors = False
            print('Cells with unexpected errors:\n_____________________________')
            for e, src in unexpected_errors:
                print(src)
                print('unexpected error: '+e)
        else:
            print('no unexpected errors')

        # Get all of the missing expected errors (logic: cell has output
        # but expected error was not generated.)
        missing_expected_errors = []
        for c in nb.cells:
            if expected_error_markup in c.metadata:
                missing_error = True
                if 'outputs' in c:
                    for output in c.outputs:
                        if (output.output_type=='error') and (c.metadata[expected_error_markup] in output.evalue):
                                missing_error = False
                if missing_error:
                    missing_expected_errors.append((c.metadata[expected_error_markup],c.source))

        no_missing_expected_errors = True
        if missing_expected_errors:
            no_missing_expected_errors = False
            print('\nCells with missing expected errors:\n___________________________________')
            for e, src in missing_expected_errors:
                print(src)
                print('missing expected error: '+e)
        else:
            print('no missing expected errors')

        print('-------- end (kernel {0}) {1} --------'.format(kernel_name,file_name))
        assert(no_unexpected_output and no_unexpected_errors and no_missing_expected_errors)


    def absolute_path_python(self, notebook_file_name):
        return os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../Python', notebook_file_name))        

    def absolute_path_r(self, notebook_file_name):
        return os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../R', notebook_file_name))

    #
    # Python notebook testing.
    #
    @pytest.mark.python_notebook
    def test_00_Setup_p(self):
        self.evaluate_notebook(self.absolute_path_python('00_Setup.ipynb'), 'python2')

    @pytest.mark.python_notebook
    def test_01_Image_Basics_p(self):
        self.evaluate_notebook(self.absolute_path_python('01_Image_Basics.ipynb'), 'python2')

    @pytest.mark.python_notebook
    def test_02_Pythonic_Image_p(self):
        self.evaluate_notebook(self.absolute_path_python('02_Pythonic_Image.ipynb'), 'python2')

    @pytest.mark.python_notebook
    def test_03_Image_Details_p(self):
        self.evaluate_notebook(self.absolute_path_python('03_Image_Details.ipynb'), 'python2')

    @pytest.mark.python_notebook
    def test_10_matplotlibs_imshow_p(self):
        self.evaluate_notebook(self.absolute_path_python('10_matplotlib\'s_imshow.ipynb'), 'python2')

    @pytest.mark.python_notebook
    def test_20_Expand_With_Interpolators_p(self):
        self.evaluate_notebook(self.absolute_path_python('20_Expand_With_Interpolators.ipynb'), 'python2')

    @pytest.mark.python_notebook
    def test_21_Transforms_and_Resampling_p(self):
        self.evaluate_notebook(self.absolute_path_python('21_Transforms_and_Resampling.ipynb'), 'python2')

    @pytest.mark.python_notebook
    def test_22_Transforms_p(self):
        self.evaluate_notebook(self.absolute_path_python('22_Transforms.ipynb'), 'python2')

    @pytest.mark.python_notebook
    def test_300_Segmentation_Overview_p(self):
        self.evaluate_notebook(self.absolute_path_python('300_Segmentation_Overview.ipynb'), 'python2')

    @pytest.mark.python_notebook
    def test_30_Segmentation_Region_Growing_p(self):
        self.evaluate_notebook(self.absolute_path_python('30_Segmentation_Region_Growing.ipynb'), 'python2')

    @pytest.mark.python_notebook
    def test_31_Levelset_Segmentation_p(self):
        self.evaluate_notebook(self.absolute_path_python('31_Levelset_Segmentation.ipynb'), 'python2')

    @pytest.mark.python_notebook
    def test_32_Watersheds_Segmentation_p(self):
        self.evaluate_notebook(self.absolute_path_python('32_Watersheds_Segmentation.ipynb'), 'python2')

    @pytest.mark.python_notebook
    def test_33_Segmentation_Thresholding_Edge_Detection_p(self):
        self.evaluate_notebook(self.absolute_path_python('33_Segmentation_Thresholding_Edge_Detection.ipynb'), 'python2')

    @pytest.mark.python_notebook
    def test_34_Segmentation_Evaluation_p(self):
        self.evaluate_notebook(self.absolute_path_python('34_Segmentation_Evaluation.ipynb'), 'python2')

    # This notebook times out when run with nbconvert, due to javascript issues. We currently don't
    # test it.
    @pytest.mark.python_notebook
    def test_41_Progress_p(self):
        #self.evaluate_notebook(self.absolute_path_python('41_Progress.ipynb'), 'python2')
        assert(True)

    @pytest.mark.python_notebook
    def test_51_VH_Segmentation1_p(self):
        self.evaluate_notebook(self.absolute_path_python('51_VH_Segmentation1.ipynb'), 'python2')

    # This notebook uses too much memory (exceeds the 4Gb allocated for the testing machine).
    @pytest.mark.large_memory
    @pytest.mark.python_notebook
    def test_55_VH_Resample_p(self):
        self.evaluate_notebook(self.absolute_path_python('55_VH_Resample.ipynb'), 'python2')

    @pytest.mark.python_notebook
    def test_56_VH_Registration1_p(self):
        self.evaluate_notebook(self.absolute_path_python('56_VH_Registration1.ipynb'), 'python2')

    @pytest.mark.python_notebook
    def test_60_Registration_Introduction_p(self):
        self.evaluate_notebook(self.absolute_path_python('60_Registration_Introduction.ipynb'), 'python2')

    # This notebook uses too much memory (exceeds the 4Gb allocated for the testing machine).
    @pytest.mark.large_memory
    @pytest.mark.python_notebook
    def test_61_Registration_Introduction_Continued_p(self):
        self.evaluate_notebook(self.absolute_path_python('61_Registration_Introduction_Continued.ipynb'), 'python2')

    @pytest.mark.python_notebook
    def test_62_Registration_Tuning_p(self):
        self.evaluate_notebook(self.absolute_path_python('62_Registration_Tuning.ipynb'), 'python2')

    @pytest.mark.python_notebook
    def test_63_Registration_Initialization_p(self):
        self.evaluate_notebook(self.absolute_path_python('63_Registration_Initialization.ipynb'), 'python2')

    @pytest.mark.python_notebook
    def test_64_Registration_Memory_Time_Tradeoff_p(self):
        self.evaluate_notebook(self.absolute_path_python('64_Registration_Memory_Time_Tradeoff.ipynb'), 'python2')

    @pytest.mark.python_notebook
    def test_65_Registration_FFD_p(self):
        self.evaluate_notebook(self.absolute_path_python('65_Registration_FFD.ipynb'), 'python2')

    # This notebook uses too much memory (exceeds the 4Gb allocated for the testing machine).
    @pytest.mark.large_memory
    @pytest.mark.python_notebook
    def test_66_Registration_Demons_p(self):
        self.evaluate_notebook(self.absolute_path_python('66_Registration_Demons.ipynb'), 'python2')

    @pytest.mark.python_notebook
    def test_67_Registration_Semiautomatic_Homework_p(self):
        self.evaluate_notebook(self.absolute_path_python('67_Registration_Semiautomatic_Homework.ipynb'), 'python2')



