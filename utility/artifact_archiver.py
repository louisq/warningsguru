"""
The MIT License (MIT)

Copyright (c) 2016 Louis-Philippe Querel l_querel@encs.concordia.ca

Permission is hereby granted, free of charge, to any person obtaining a copy of this software
and associated documentation files (the "Software"), to deal in the Software without restriction,
including without limitation the rights to use, copy, modify, merge, publish, distribute,
sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or
substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING
BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
import glob
import os
import shutil

from Logging import logger

"""
The purpose of this utility is to clone the artifacts that have been generated through the build process to preserve them
This version would probably only work for maven run projects
"""

FILTERED_EXTENSIONS = ('*.jar', '*.tar.*', '*.zip', '*.rpm')

# todo replace with an abstract solution that could be reused for the other modules to log the version that was ran
artifact_archiver_version = 1


def archive(repo_path, archive_path, repo_id, commit, filter_extensions=True):

    # Determine if we can access the path where the archive should be
    if not _determine_access(archive_path):
        logger.error("Failed to save to archive %s" % archive_path)
        return False

    temp_archive = os.path.join(repo_path, "%s-temp" % commit)
    temp_archive_compress_file_no_ext = os.path.join(temp_archive, commit)
    temp_archive_compress_file = "%s.tar.gz" % temp_archive_compress_file_no_ext

    archive_repo_path = os.path.join(archive_path, repo_id)
    archive_compress_file = "%s.tar.gz" % os.path.join(archive_repo_path, commit)

    _clear_archive(temp_archive, archive_compress_file)
    
    target_directories = _identify_target_directories(repo_path)

    _clone_files_in_targets(repo_path, temp_archive, target_directories, filter_extensions=filter_extensions)

    _compress_files(temp_archive, temp_archive_compress_file_no_ext)

    _move_compress_file_to_archive(archive_repo_path, temp_archive_compress_file)

    # Delete the temporary folder
    _clear_archive_temp(temp_archive)

    return True


def _determine_access(archive_path):
    return os.path.exists(archive_path)


def _clear_archive(archive_temp, archive_compress_file):

    _clear_archive_temp(archive_temp)

    if os.path.exists(archive_compress_file):
        os.remove(archive_compress_file)


def _clear_archive_temp(temp_archive):
    if os.path.exists(temp_archive):
        shutil.rmtree(temp_archive)
        
        
def _identify_target_directories(repo_path):
    folder = "target"
    nesting = "**/"

    target_directories = glob.glob(r'%s%s' % (repo_path, folder))

    compound_nesting = ""

    # We need to navigate the repository to find project target folders
    for count in range(5):
        compound_nesting += nesting
        target_directories += glob.glob(r'%s%s%s' % (repo_path, compound_nesting, folder))

    return target_directories


def _clone_files_in_targets(repo_path, temp_archive, target_directories, filter_extensions):

    # Determine if we need to filter any of the files
    if filter_extensions:
        ignore = shutil.ignore_patterns(FILTERED_EXTENSIONS)
    else:
        ignore = None

    for path in target_directories:
        folder = path[len(repo_path):]
        shutil.copytree(path, "%s/%s" % (temp_archive, folder), ignore=ignore, symlinks=True)


def _compress_files(archive_temp, temp_archive_compress_file_no_ext):

    # If the compression is changed the file extension needs to be changed as well in the parent method
    shutil._make_tarball(temp_archive_compress_file_no_ext, archive_temp, compress="gzip")


def _move_compress_file_to_archive(repo_archive_path, temp_archive_compress_file):

    if not os.path.exists(repo_archive_path):
        os.makedirs(repo_archive_path)

    shutil.move(temp_archive_compress_file, repo_archive_path)
