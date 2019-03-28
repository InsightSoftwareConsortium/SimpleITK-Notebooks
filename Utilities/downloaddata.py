#!/usr/bin/env python

"""
Since we do not want to store large binary data files in our Git repository,
we fetch_data_all from a network resource.

The data we download is described in a json file. The file format is a dictionary
of dictionaries. The top level key is the file name. The returned dictionary
contains a sha512 checksum and possibly a url and boolean flag indicating
the file is part of an archive. The sha512 checksum is mandatory.
When the optional url is given, we attempt to download from that url, otherwise
we attempt to download from the list of servers returned by the
get_servers() function. Files that are contained in archives are
identified by the archive flag.

Example json file contents:

{
 "SimpleITK.jpg": {
  "sha512": "f1b5ce1bf9d7ebc0bd66f1c3bc0f90d9e9798efc7d0c5ea7bebe0435f173355b27df632971d1771dc1fc3743c76753e6a28f6ed43c5531866bfa2b38f1b8fd46"
 },
 "POPI/meta/00-P.mhd": {
  "url": "http://tux.creatis.insa-lyon.fr/~srit/POPI/Images/MetaImage/00-MetaImage.tar",
  "archive": "true",
  "sha512": "09fcb39c787eee3822040fcbf30d9c83fced4246c518a24ab14537af4b06ebd438e2f36be91e6e26f42a56250925cf1bfa0d2f2f2192ed2b98e6a9fb5f5069fc"
 },
 "CIRS057A_MR_CT_DICOM/readme.txt": {
  "archive": "true",
  "sha512": "d5130cfca8467c4efe1c6b4057684651d7b74a8e7028d9402aff8e3d62287761b215bc871ad200d4f177b462f7c9358f1518e6e48cece2b51c6d8e3bb89d3eef"
 }
}

Notes: 
1. The file we download can be inside an archive. In this case, the sha512
checksum is that of the archive.

"""

import hashlib
import sys
import os
import json

import errno
import warnings

# http://stackoverflow.com/questions/2028517/python-urllib2-progress-hook

def url_download_report(bytes_so_far, url_download_size, total_size):
    percent = float(bytes_so_far) / total_size
    percent = round(percent * 100, 2)
    if bytes_so_far > url_download_size:
        # Note that the carriage return is at the begining of the
        # string and not the end. This accomodates usage in 
        # IPython usage notebooks. Otherwise the string is not
        # displayed in the output.
        sys.stdout.write("\rDownloaded %d of %d bytes (%0.2f%%)" %
                         (bytes_so_far, total_size, percent))
        sys.stdout.flush()
    if bytes_so_far >= total_size:
        sys.stdout.write("\rDownloaded %d of %d bytes (%0.2f%%)\n" %
                         (bytes_so_far, total_size, percent))
        sys.stdout.flush()
        
 
def url_download_read(url, outputfile, url_download_size=8192 * 2, report_hook=None):
    # Use the urllib2 to download the data. The Requests package, highly
    # recommended for this task, doesn't support the file scheme so we opted
    # for urllib2 which does.  

    try:
        # Python 3
        from urllib.request import urlopen, URLError, HTTPError
    except ImportError:
        from urllib2 import urlopen, URLError, HTTPError
    from xml.dom import minidom
    
    # Open the url
    try:
        url_response = urlopen(url)
    except HTTPError as e:
        return "HTTP Error: {0} {1}\n".format(e.code, url)
    except URLError as e:
        return "URL Error: {0} {1}\n".format(e.reason, url)

    # We download all content types - the assumption is that the sha512 ensures
    # that what we received is the expected data.
    try:
        # Python 3
        content_length = url_response.info().get("Content-Length")
    except AttributeError:
        content_length = url_response.info().getheader("Content-Length")
    total_size = content_length.strip()
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

#http://stackoverflow.com/questions/2536307/decorators-in-the-python-standard-lib-deprecated-specifically
def deprecated(func):
    """This is a decorator which can be used to mark functions
    as deprecated. It will result in a warning being emmitted
    when the function is used."""

    def new_func(*args, **kwargs):
        warnings.simplefilter('always', DeprecationWarning) #turn off filter 
        warnings.warn("Call to deprecated function {}.".format(func.__name__), category=DeprecationWarning, stacklevel=2)
        warnings.simplefilter('default', DeprecationWarning) #reset filter
        return func(*args, **kwargs)

    new_func.__name__ = func.__name__
    new_func.__doc__ = func.__doc__
    new_func.__dict__.update(func.__dict__)
    return new_func

def get_servers():
    import os
    servers = list()
    # NIAID S3 data store
    servers.append( "https://s3.amazonaws.com/simpleitk/public/notebooks/SHA512/%(hash)" )
    # Girder server hosted by kitware
    servers.append("https://data.kitware.com/api/v1/file/hashsum/sha512/%(hash)/download")
    # Local file store
    if 'ExternalData_OBJECT_STORES' in os.environ.keys():
        local_object_stores = os.environ['ExternalData_OBJECT_STORES']
        for local_object_store in local_object_stores.split(";"):
          servers.append( "file://{0}/SHA512/%(hash)".format(local_object_store) )
    return servers


def output_hash_is_valid(known_sha512, output_file):
    sha512 = hashlib.sha512()
    if not os.path.exists(output_file):
        return False
    with open(output_file, 'rb') as fp:
        for url_download in iter(lambda: fp.read(128 * sha512.block_size), b''):
            sha512.update(url_download)
    retreived_sha512 = sha512.hexdigest()
    return retreived_sha512 == known_sha512


def fetch_data_one(onefilename, output_directory, manifest_file, verify=True, force=False):
    import tarfile, zipfile
    
    with open(manifest_file, 'r') as fp:
        manifest = json.load(fp)
    assert onefilename in manifest, "ERROR: {0} does not exist in {1}".format(onefilename, manifest_file)

    sys.stdout.write("Fetching {0}\n".format(onefilename))
    output_file = os.path.realpath(os.path.join(output_directory, onefilename))
    data_dictionary = manifest[onefilename]
    sha512 = data_dictionary['sha512']
    # List of places where the file can be downloaded from
    all_urls = []
    for url_base in get_servers():
        all_urls.append(url_base.replace("%(hash)", sha512))
    if "url" in data_dictionary:
        all_urls.append(data_dictionary["url"])    
        
    new_download = False

    for url in all_urls:
        # Only download if force is true or the file does not exist.
        if force or not os.path.exists(output_file):
            mkdir_p(os.path.dirname(output_file))
            url_download_read(url, output_file, report_hook=url_download_report)
            # Check if a file was downloaded and has the correct hash
            if output_hash_is_valid(sha512, output_file):
                new_download = True
                # Stop looking once found
                break
            # If the file exists this means the hash is invalid we have a problem.
            elif os.path.exists(output_file):
                    error_msg = "File " + output_file
                    error_msg += " has incorrect hash value, " + sha512 + " was expected."
                    raise Exception(error_msg)

    # Did not find the file anywhere.        
    if not os.path.exists(output_file):
        error_msg = "File " + "\'"  + os.path.basename(output_file) +"\'"
        error_msg += " could not be found in any of the following locations:\n" 
        error_msg += ", ".join(all_urls)
        raise Exception(error_msg)
    
    if not new_download and verify:
        # If the file was part of an archive then we don't verify it. These
        # files are only verfied on download
        if ( not "archive" in data_dictionary) and ( not output_hash_is_valid(sha512, output_file) ):
            # Attempt to download if sha512 is incorrect.
            fetch_data_one(onefilename, output_directory, manifest_file, verify, 
                           force=True)
    # If the file is in an archive, unpack it.                          
    if tarfile.is_tarfile(output_file) or zipfile.is_zipfile(output_file):
        tmp_output_file = output_file + ".tmp"
        os.rename(output_file, tmp_output_file)        
        if tarfile.is_tarfile(tmp_output_file):
            archive = tarfile.open(tmp_output_file)
        if zipfile.is_zipfile(tmp_output_file):
            archive = zipfile.ZipFile(tmp_output_file, 'r')
        archive.extractall(os.path.dirname(tmp_output_file))
        archive.close()
        os.remove(tmp_output_file)

    return output_file


def fetch_data_all(output_directory, manifest_file, verify=True):
    with open(manifest_file, 'r') as fp:
        manifest = json.load(fp)
    for filename in manifest:
        fetch_data_one(filename, output_directory, manifest_file, verify, 
                       force=False)

def fetch_data(cache_file_name, verify=False, cache_directory_name="../Data"):
    """
    fetch_data is a simplified interface that requires
    relative pathing with a manifest.json file located in the
    same cache_directory_name name.

    By default the cache_directory_name is "Data" relative to the current
    python script.  An absolute path can also be given.
    """
    if not os.path.isabs(cache_directory_name):
        cache_root_directory_name = os.path.dirname(__file__)
        cache_directory_name = os.path.join(cache_root_directory_name, cache_directory_name)
    cache_manifest_file = os.path.join(cache_directory_name, 'manifest.json')
    assert os.path.exists(cache_manifest_file), "ERROR, {0} does not exist".format(cache_manifest_file)
    return fetch_data_one(cache_file_name, cache_directory_name, cache_manifest_file, verify=verify)


if __name__ == '__main__':
    
        
    if len(sys.argv) < 3:
        print('Usage: ' + sys.argv[0] + ' output_directory manifest.json')
        sys.exit(1)
    output_directory = sys.argv[1]
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    manifest = sys.argv[2]
    fetch_data_all(output_directory, manifest)
