#!/usr/bin/env python

"""
Since we do not want to store large binary data files in our Git repository,
we fetch_midas_data_all it from a network resource.
"""

import hashlib
import sys
import os
import json

import errno

# http://stackoverflow.com/questions/2028517/python-urllib2-progress-hook


def url_download_report(bytes_so_far, url_download_size, total_size):
    percent = float(bytes_so_far) / total_size
    percent = round(percent * 100, 2)
    if bytes_so_far > url_download_size:
        sys.stdout.write("Downloaded %d of %d bytes (%0.2f%%)\r" %
                         (bytes_so_far, total_size, percent))
    if bytes_so_far >= total_size:
        sys.stdout.write('\n')


def url_download_read(url, outputfile, url_download_size=8192 * 2, report_hook=None):
    from urllib2 import urlopen, URLError, HTTPError
    # Open the url
    try:
        url_response = urlopen(url)
    except HTTPError as e:
        return "HTTP Error: {0} {1}\n".format(e.code, url)
    except URLError as e:
        return "URL Error: {0} {1}\n".format(e.reason, url)
    total_size = url_response.info().getheader('Content-Length').strip()
    total_size = int(total_size)
    bytes_so_far = 0
    with open(outputfile, "wb") as local_file:
        while 1:
            try:
                url_download = url_response.read(url_download_size)
                bytes_so_far += len(url_download)
                if not url_download:
                    break
                local_file.write(url_download)
            # handle errors
            except HTTPError as e:
                return "HTTP Error: {0} {1}\n".format(e.code, url)
            except URLError as e:
                return "URL Error: {0} {1}\n".format(e.reason, url)
            if report_hook:
                report_hook(bytes_so_far, url_download_size, total_size)
    return "Downloaded Successfully"


# http://stackoverflow.com/questions/600268/mkdir-p-functionality-in-python?rq=1
def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise
def get_midas_servers():
    import os
    midas_servers = list()
    if 'ExternalData_OBJECT_STORES' in os.environ.keys():
        local_object_stores = os.environ['ExternalData_OBJECT_STORES']
        for local_object_store in local_object_stores.split(";"):
          midas_servers.append( "file://{0}/MD5/%(hash)".format(local_object_store) )
    midas_servers.extend( [
        # Data published by MIDAS
        "http://midas3.kitware.com/midas/api/rest?method=midas.bitstream.download&checksum=%(hash)&algorithm=%(algo)",
        # Data published by developers using git-gerrit-push.
        "http://www.itk.org/files/ExternalData/%(algo)/%(hash)",
        # Mirror supported by the Slicer community.
        "http://slicer.kitware.com/midas3/api/rest?method=midas.bitstream.download&checksum=%(hash)&algorithm=%(algo)",
        ])
    return midas_servers


def output_hash_is_valid(known_md5sum, output_file):
    md5 = hashlib.md5()
    if not os.path.exists(output_file):
        return False
    with open(output_file, 'rb') as fp:
        for url_download in iter(lambda: fp.read(128 * md5.block_size), b''):
            md5.update(url_download)
    retreived_md5sum = md5.hexdigest()
    return retreived_md5sum == known_md5sum


def fetch_midas_data_one(onefilename, output_directory, manifest_file, verify=True, force=False):
    with open(manifest_file, 'r') as fp:
        manifest = json.load(fp)
    for filename, md5sum in manifest:
        if filename == onefilename:
            break
    assert filename == onefilename, "ERROR: {0} does not exist in {1}".format(onefilename, manifest_file)

    output_file = os.path.realpath(os.path.join(output_directory, onefilename))
    for url_base in get_midas_servers():
        url = url_base.replace("%(hash)", md5sum).replace("%(algo)", "md5")
        if not os.path.exists(output_file):
            verify = True  # Must verify if the file does not exists originally
        # Only download if the file does not already exist.
        errorMsg = ""
        if force or not os.path.exists(output_file):
            mkdir_p(os.path.dirname(output_file))
            errorMsg += url_download_read(url, output_file, report_hook=url_download_report)
            if output_hash_is_valid(md5sum, output_file):
                # Stop looking once found at one of the midas servers!
                verify = False  # No need to re-verify
                errorMsg = "Verified download for {0}".format(output_file)
                break

    if verify:
        if force == True and ( not output_hash_is_valid(md5sum, output_file) ):
            error_msg = 'File ' + output_file
            error_msg += ' has incorrect hash value, ' + md5sum + ' was expected.'
            raise Exception(error_msg)
        if force == False and ( not output_hash_is_valid(md5sum, output_file) ):
            # Attempt to download if md5sum is incorrect.
            fetch_midas_data_one(onefilename, output_directory, manifest_file, verify, force=True)
    if len(errorMsg) > 0:
        print(errorMsg)
    return output_file


def fetch_midas_data_all(output_directory, manifest_file, verify=True):
    with open(manifest_file, 'r') as fp:
        manifest = json.load(fp)
    for filename, _ in manifest:
        fetch_midas_data_one(filename, output_directory, manifest_file, verify=True, force=False)


def fetch_midas_data(cache_file_name, verify=False, cache_directory_name="Data"):
    """
    fetch_midas_data is a simplified interface that requires
    relative pathing with a manifest.json file located in the
    same cache_directory_name name.

    By default the cache_directory_name is "Data" relative to the current
    python script.  An absolute path can also be given
    """
    if not os.path.isabs(cache_directory_name):
        cache_root_directory_name = os.path.dirname(__file__)
        cache_directory_name = os.path.join(cache_root_directory_name, cache_directory_name)
    cache_manifest_file = os.path.join(cache_directory_name, 'manifest.json')
    assert os.path.exists(cache_manifest_file), "ERROR, {0} does not exist".format(cache_manifest_file)
    return fetch_midas_data_one(cache_file_name, cache_directory_name, cache_manifest_file, verify=verify)

if __name__ == '__main__':
    import time

    if len(sys.argv) < 3:
        print('Usage: ' + sys.argv[0] + ' output_directory manifest.json')
        sys.exit(1)
    output_directory = sys.argv[1]
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    manifest = sys.argv[2]
    fetch_midas_data_all(output_directory, manifest)
