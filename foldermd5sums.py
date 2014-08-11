#!/usr/bin/env python

"""Script to read data files in a directory, compute their md5sums, and output
them to a JSON file."""

import json
import os
import sys
import hashlib


def get_relative_filepaths(base_directory):
    """ Return a list of file paths without the base_directory prefix"""
    file_list = []
    for root, subFolders, files in os.walk('Data'):
        relative_path = "/".join(root.split('/')[1:])
        for file in files:
            file_list.append(os.path.join(relative_path, file))
    return file_list


def get_md5sums(base_directory):
    md5sums = []
    for filename in get_relative_filepaths(base_directory):
        if ".json" in filename:
            continue ## Skipping the hash entry for all .json files
        md5 = hashlib.md5()
        full_filepath = os.path.join(base_directory, filename)
        with open(full_filepath, 'rb') as fp:
            for chunk in iter(lambda: fp.read(128 * md5.block_size), b''):
                md5.update(chunk)
        md5hash = md5.hexdigest()
        md5sums.append((filename, md5hash))
    return md5sums

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Usage: ' + sys.argv[0] + ' input_directory output.json')
        sys.exit(1)
    directory = sys.argv[1]
    if not os.path.exists(directory):
        print('Directory does not exist!')
        sys.exit(1)
    output_json = sys.argv[2]

    md5sums = get_md5sums(directory)
    with open(output_json, 'w') as fp:
        json.dump(md5sums, fp, indent=0)
