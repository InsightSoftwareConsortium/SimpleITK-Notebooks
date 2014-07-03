#!/usr/bin/env python

"""Script to read data files in a directory, compute their md5sums, and output
them to a JSON file."""

import json
import os
import sys
import hashlib

def get_md5sums(directory):
    md5sums = []
    for filename in os.listdir(directory):
        md5 = hashlib.md5()
        with open(os.path.join(directory, filename), 'rb') as fp:
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
