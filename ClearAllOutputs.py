#!/usr/bin/env python
## This script was from a stack-overflow recommendation hosted on a github gist
"""strip outputs from an IPython Notebook
 
Opens a notebook, strips its output, and writes the outputless version to the original file.
 
Useful mainly as a git pre-commit hook for users who don't want to track output in VCS.
 
This does mostly the same thing as the `Clear All Output` command in the notebook UI.
"""
 
import io
import sys
 
from IPython.nbformat import current
 
def strip_output(nb):
    """strip the outputs from a notebook object"""
    nb.metadata.pop('signature', None)
    for cell in nb.worksheets[0].cells:
        if 'outputs' in cell:
            cell['outputs'] = []
        if 'prompt_number' in cell:
            cell['prompt_number'] = None
    return nb
 
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "USAGE: {0} <filename.ipynb>".format(sys.argv[0])
        print ""
        print "for i in *.ipynb; do ./{0} $i; done".format(sys.argv[0])
        sys.exit(-1)
    filename = sys.argv[1]
    with io.open(filename, 'r', encoding='utf8') as f:
        nb = current.read(f, 'json')
    nb_out = strip_output(nb)
    if nb != nb_out:
        with io.open(filename, 'w', encoding='utf8') as f:
            current.write(nb_out, f, 'json')
        sys.exit(1)
    sys.exit(0)
