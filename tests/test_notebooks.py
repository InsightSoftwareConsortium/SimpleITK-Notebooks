import os
import subprocess
import tempfile
import nbformat
import pytest
import markdown
import re

from enchant.checker import SpellChecker
from enchant.tokenize import Filter, EmailFilter, URLFilter
from enchant import DictWithPWL

from lxml.html import document_fromstring, etree
try:
   # Python 3
   from urllib.request import urlopen, URLError
except ImportError:
   from urllib2 import urlopen, URLError



"""
run all tests:
pytest -v --tb=short

run python tests:
pytest -v --tb=short tests/test_notebooks.py::Test_notebooks::test_python_notebook

run r tests:
pytest -v --tb=short tests/test_notebooks.py::Test_notebooks::test_r_notebook

run specific Python test:
pytest -v --tb=short tests/test_notebooks.py::Test_notebooks::test_python_notebook[00_Setup.ipynb]

run specific R test:
pytest -v --tb=short tests/test_notebooks.py::Test_notebooks::test_r_notebook[00_Setup.ipynb]

-s : disable all capturing of output.
"""

class Test_notebooks(object):
    """
    Testing of SimpleITK Jupyter notebooks:
    1. Static analysis:
       Check that notebooks do not contain output (sanity check as these should
       not have been pushed to the repository).
       Check that all the URLs in the markdown cells are not broken.
    2. Dynamic analysis:
       Run the notebook and check for errors. In some notebooks we
       intentionally cause errors to illustrate certain features of the toolkit. 
       All code cells that intentionally generate an error are expected to be 
       marked using the cell's metadata. In the notebook go to 
       "View->Cell Toolbar->Edit Metadata and add the following json entry:
       
       "simpleitk_error_expected": simpleitk_error_message

       with the appropriate "simpleitk_error_message" text.
       Cells where an error is allowed, but not necessarily expected should be
       marked with the following json:

       "simpleitk_error_allowed": simpleitk_error_message

       The simpleitk_error_message is a substring of the generated error
       message, such as 'Exception thrown in SimpleITK Show:'

    To test notebooks that use too much memory (exceed the 4Gb allocated for the testing
    machine):
    1. Create an enviornment variable named SIMPLE_ITK_MEMORY_CONSTRAINED_ENVIRONMENT
    2. Import the setup_for_testing.py at the top of the notebook. This module will
       decorate the sitk.ReadImage so that after reading the initial image it is
       resampled by a factor of 4 in each dimension.

    Adding a test:
    Simply add the new notebook file name to the list of files decorating the test_python_notebook
    or test_r_notebook functions. DON'T FORGET THE COMMA.
    """

    _allowed_error_markup = 'simpleitk_error_allowed'
    _expected_error_markup = 'simpleitk_error_expected'

    @pytest.mark.parametrize('notebook_file_name',
                             ['00_Setup.ipynb',
                              '01_Image_Basics.ipynb',
                              '02_Pythonic_Image.ipynb',
                              '03_Image_Details.ipynb',
                              '04_Image_Display.ipynb',
                              '05_Results_Visualization.ipynb',
                              '10_matplotlib\'s_imshow.ipynb',
                              '20_Expand_With_Interpolators.ipynb',
                              '21_Transforms_and_Resampling.ipynb',
                              '22_Transforms.ipynb',
                              '300_Segmentation_Overview.ipynb',
                              '30_Segmentation_Region_Growing.ipynb',
                              '31_Levelset_Segmentation.ipynb',
                              '32_Watersheds_Segmentation.ipynb',
                              '33_Segmentation_Thresholding_Edge_Detection.ipynb',
                              '34_Segmentation_Evaluation.ipynb',
                              pytest.param('35_Segmentation_Shape_Analysis.ipynb', marks=pytest.mark.skipif(os.environ.get('CIRCLECI')=='true', \
                                                                                                            reason="runtime too long for CircleCI")),
                              '36_Microscopy_Colocalization_Distance_Analysis.ipynb',
                              #'11_Progress.ipynb', # This notebook times out when run with nbconvert, due to javascript issues, so not tested.
                              '51_VH_Segmentation1.ipynb',
                              '55_VH_Resample.ipynb',
                              '56_VH_Registration1.ipynb',
                              '60_Registration_Introduction.ipynb',
                              '61_Registration_Introduction_Continued.ipynb',
                              '62_Registration_Tuning.ipynb',
                              '63_Registration_Initialization.ipynb',
                              '64_Registration_Memory_Time_Tradeoff.ipynb',
                              '65_Registration_FFD.ipynb',
                              '66_Registration_Demons.ipynb',
                              '67_Registration_Semiautomatic_Homework.ipynb',
                              '68_Registration_Errors.ipynb',
                              '69_x-ray-panorama.ipynb',
                              '70_Data_Augmentation.ipynb'])
    def test_python_notebook(self, notebook_file_name):
       self.evaluate_notebook(self.absolute_path_python(notebook_file_name), 'python')


    @pytest.mark.parametrize('notebook_file_name',
                             ['00_Setup.ipynb',
                              'Image_Basics.ipynb',
                              'R_style_image.ipynb',
                              '33_Segmentation_Thresholding_Edge_Detection.ipynb',
                              '34_Segmentation_Evaluation.ipynb',
                              '35_Cell_Segmentation.ipynb',
                              '22_Transforms.ipynb',
                              '300_Segmentation_Overview.ipynb',
                              '60_Registration_Introduction.ipynb',
                              '61_Registration_Introduction_Continued.ipynb',
                              '65_Registration_FFD.ipynb',
                              '66_Registration_Demons.ipynb',
                              '70_Data_Augmentation.ipynb'])
    def test_r_notebook(self, notebook_file_name):
       self.evaluate_notebook(self.absolute_path_r(notebook_file_name), 'ir')

    def evaluate_notebook(self, path, kernel_name):
        """
        Perform static and dynamic analysis of the notebook.
        Execute a notebook via nbconvert and print the results of the test (errors etc.)
        Args:
            path (string): Name of notebook to run.
            kernel_name (string): Which jupyter kernel to use to run the test. 
                                  Relevant values are:'python2', 'python3', 'ir'.
        """

        dir_name, file_name = os.path.split(path)
        if dir_name:
            os.chdir(dir_name)

        print('-------- begin (kernel {0}) {1} --------'.format(kernel_name,file_name))
        no_static_errors = self.static_analysis(path)
        no_dynamic_errors = self.dynamic_analysis(path, kernel_name)
        print('-------- end (kernel {0}) {1} --------'.format(kernel_name,file_name))
        assert(no_static_errors and no_dynamic_errors)


    def static_analysis(self, path):
        """
        Perform static analysis of the notebook.
        Read the notebook and check that there is no ouput and that the links
        in the markdown cells are not broken.
        Args:
            path (string): Name of notebook.
        Return:
            boolean: True if static analysis succeeded, otherwise False.
        """

        nb = nbformat.read(path, nbformat.current_nbformat)

        #######################
        # Check that the notebook does not contain output from code cells 
        # (should not be in the repository, but well...).
        #######################
        no_unexpected_output = True

        # Check that the cell dictionary has an 'outputs' key and that it is
        # empty, relies on Python using short circuit evaluation so that we
        # don't get KeyError when retrieving the 'outputs' entry.
        cells_with_output = [c.source for c in nb.cells if 'outputs' in c and c.outputs]
        if cells_with_output:
            no_unexpected_output = False
            print('Cells with unexpected output:\n_____________________________')
            for cell in cells_with_output: 
                print(cell+'\n---')
        else:
           print('no unexpected output')

        #######################
        # Check that all the links in the markdown cells are valid/accessible.
        #######################
        no_broken_links = True

        cells_and_broken_links = []
        for c in nb.cells:
           if c.cell_type == 'markdown':
              html_tree = document_fromstring(markdown.markdown(c.source))
              broken_links = []
              #iterlinks() returns tuples of the form (element, attribute, link, pos)
              for document_link in html_tree.iterlinks():
                 try:
                    if all( prefix not in document_link[2] for prefix in ['http','https']):  # Local file.
                       url = 'file://' + os.path.abspath(document_link[2])
                    else:  # Remote file.
                       url = document_link[2]
                    urlopen(url)
                 except URLError:
                    broken_links.append(url)
              if broken_links:
                 cells_and_broken_links.append((broken_links,c.source))
        if cells_and_broken_links:
           no_broken_links = False
           print('Cells with broken links:\n________________________')
           for links, cell in cells_and_broken_links:
              print(cell+'\n')
              print('\tBroken links:')
              print('\t'+'\n\t'.join(links)+'\n---')
        else:
           print('no broken links')

        #######################
        # Spell check all markdown cells and comments in code cells using the pyenchant spell checker.
        #######################
        no_spelling_mistakes = True
        simpleitk_notebooks_dictionary = DictWithPWL('en_US', os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                     'additional_dictionary.txt'))
        spell_checker = SpellChecker(simpleitk_notebooks_dictionary, filters = [EmailFilter, URLFilter])
        cells_and_spelling_mistakes = []
        for c in nb.cells:
           spelling_mistakes = []
           if c.cell_type == 'markdown':
              # Get the text as a string from the html without the markup which is replaced by space.
              spell_checker.set_text(' '.join(etree.XPath('//text()')(document_fromstring(markdown.markdown(c.source)))))
           elif c.cell_type == 'code':
              # Get all the comments and concatenate them into a single string separated by newlines.
              comment_lines = re.findall('#+.*',c.source)
              spell_checker.set_text('\n'.join(comment_lines))
           for error in spell_checker:
              error_message = 'error: '+ '\'' + error.word +'\', ' + 'suggestions: ' + str(spell_checker.suggest())
              spelling_mistakes.append(error_message)
           if spelling_mistakes:
              cells_and_spelling_mistakes.append((spelling_mistakes, c.source))
        if cells_and_spelling_mistakes:
           no_spelling_mistakes = False
           print('Cells with spelling mistakes:\n________________________')
           for misspelled_words, cell in cells_and_spelling_mistakes:
              print(cell+'\n')
              print('\tMisspelled words and suggestions:')
              print('\t'+'\n\t'.join(misspelled_words)+'\n---')
        else:
           print('no spelling mistakes')

        return(no_unexpected_output and no_broken_links and no_spelling_mistakes)


    def dynamic_analysis(self, path, kernel_name):
        """
        Perform dynamic analysis of the notebook.
        Execute a notebook via nbconvert and print the results of the test
        (errors etc.)
        Args:
            path (string): Name of notebook to run.
            kernel_name (string): Which jupyter kernel to use to run the test.
                                  Relevant values are:'python', 'ir'.
        Return:
            boolean: True if dynamic analysis succeeded, otherwise False.
        """

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
                               (((Test_notebooks._allowed_error_markup not in c.metadata) and (Test_notebooks._expected_error_markup not in c.metadata))or \
                               ((Test_notebooks._allowed_error_markup in c.metadata) and (c.metadata[Test_notebooks._allowed_error_markup] not in output.evalue)) or \
                               ((Test_notebooks._expected_error_markup in c.metadata) and (c.metadata[Test_notebooks._expected_error_markup] not in output.evalue)))]
        
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
            if Test_notebooks._expected_error_markup in c.metadata:
                missing_error = True
                if 'outputs' in c:
                    for output in c.outputs:
                        if (output.output_type=='error') and (c.metadata[Test_notebooks._expected_error_markup] in output.evalue):
                                missing_error = False
                if missing_error:
                    missing_expected_errors.append((c.metadata[Test_notebooks._expected_error_markup],c.source))

        no_missing_expected_errors = True
        if missing_expected_errors:
            no_missing_expected_errors = False
            print('\nCells with missing expected errors:\n___________________________________')
            for e, src in missing_expected_errors:
                print(src)
                print('missing expected error: '+e)
        else:
            print('no missing expected errors')

        return(no_unexpected_errors and no_missing_expected_errors)


    def absolute_path_python(self, notebook_file_name):
        return os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../Python', notebook_file_name))        

    def absolute_path_r(self, notebook_file_name):
        return os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../R', notebook_file_name))
