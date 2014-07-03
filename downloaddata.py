#!/usr/bin/env python

"""
Since we do not want to store large binary data files in our Git repository,
we download it from a network resource.
"""

import hashlib
import sys
import os
import json
import urllib

OUTPUT_DIRECTORY = 'Data'
MANIFEST_FILE = os.path.join(os.path.dirname(__file__), 'Data', 'manifest.json')

def download(output_directory, manifest_file, verify=True):
    with open(manifest_file, 'r') as fp:
        manifest = json.load(fp)
    for filename, md5sum in manifest:
        url = 'https://midas3.kitware.com/midas/rest/bitstream/download?checksum='
        url = url + md5sum
        output_file = os.path.join(output_directory, filename)
        urllib.urlretrieve(url, output_file)
        if verify:
            md5 = hashlib.md5()
            with open(output_file, 'rb') as fp:
                for chunk in iter(lambda: fp.read(128 * md5.block_size), b''):
                    md5.update(chunk)
            retreived_md5sum = md5.hexdigest()
            if retreived_md5sum != md5sum:
                error_msg = 'File ' + output_file
                error_msg += ' has md5sum ' + retreived_md5sum
                error_msg += ' when ' + md5sum + ' was expected.'
                raise Exception(error_msg)

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Usage: ' + sys.argv[0] + ' output_directory manifest.json')
        sys.exit(1)
    output_directory = sys.argv[1]
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    manifest = sys.argv[2]
    download(output_directory, manifest)
else:
    download(OUTPUT_DIRECTORY, MANIFEST_FILE)
