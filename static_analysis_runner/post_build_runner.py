"""
The MIT License (MIT)

Copyright (c) 2016-2017 Louis-Philippe Querel l_querel@encs.concordia.ca

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

import fnmatch
import os
import re
import time
import subprocess

import config
from utility.Logging import logger

maximum_number_of_processes = 16
processes = []

HOUSE_KEEPING_PATH = os.path.join(os.path.abspath("./"), "static_analysis_runner", "Housekeeping.txt")

# TODO make class to allow multiprocessing of this component for different commits


def run(repo_path, adaptor_save_path, commit):

    list_of_allowed_extensions = ['java']
    adaptors_for_java = ["Findbugs", "Jlint"]

    # identified modified files
    modified_files = _identify_modified_files(repo_path)

    # filter modified files to only have java files

    filtered_modified_files = _filter_files(modified_files, list_of_allowed_extensions)

    compiled_files = _get_all_class_file(repo_path)

    modified_class_files, class_file_mapping = _identify_modified_class_files(filtered_modified_files, compiled_files, commit)
    logger.info("%s: Modified class files to analyse: %s" % (commit, str(modified_class_files)))

    _run_adaptors_on_files(modified_class_files, repo_path, adaptors_for_java, adaptor_save_path)

    _wait_for_processes_to_finish()

    return class_file_mapping


def _identify_modified_files(repo_path):
    from git import Repo

    repo = Repo(repo_path)
    return repo.head.commit.stats.files.keys()


def _filter_files(files, list_of_extensions):
    return filter(lambda file_name: file_name[len(file_name) - 4:].lower() in list_of_extensions, files)


FILE_PATTERN = re.compile("([\w\d_-]+)(?:\$[\w\$]*)*\.[\w\d]+")


def _get_all_class_file(repo_path):
    files_map = {}

    for path, directory, files in os.walk(repo_path):
        # Identify all f the class
        files = fnmatch.filter(files, '*.class')

        for class_file in files:
            # todo handle if the pattern fails
            name = FILE_PATTERN.match(class_file).groups()[0]

            if name not in files_map:
                files_map[name] = {}

            relative_path = path[len(repo_path)+1:]
            if relative_path not in files_map[name]:
                files_map[name][relative_path] = []

            files_map[name][relative_path].append(os.path.join(relative_path, class_file))

    return files_map


def _identify_modified_class_files(modified_files, classes, commit):

    modified_classes = []

    class_file_mapping = {}

    for modified_file in modified_files:
        split_name = modified_file.split("/")
        name = split_name[len(split_name)-1].split(".")[0]

        if name not in classes:
            logger.error("%s: Class %s not in %s" % (commit, name, str(classes)))
            continue

        modified_class = classes.get(name)

        file_modified_classes = []

        if len(modified_class) > 1:
            # if there is more then one class then it means that there are multiple files with the same name
            # In that case we therefore need to be able to determine which file was modified
            reversed_source_path = split_name[:len(split_name)-1][::-1]
            path_analysis = {}

            longest_path = ""
            longest_path_length = -1

            for modified_class_path in modified_class.keys():
                path = modified_class_path.split('/')[::-1]

                # Calculate the similarity between the path of the class file and the source file and determine which
                # one is longer
                for i in xrange(len(path)):
                    # Validate that the path is long enough for the index and if not the index is the length
                    if len(path) < i or len(reversed_source_path) < i or path[i] != reversed_source_path[i]:
                        path_analysis[modified_class_path] = i
                        if i > longest_path_length:
                            longest_path = modified_class_path
                            longest_path_length = i
                        break

            file_modified_classes = modified_class[longest_path]

        else:
            file_modified_classes = modified_class[modified_class.keys()[0]]

        modified_classes += file_modified_classes

        # make mapping of the class files to their respective original files
        for class_file in file_modified_classes:
            class_file_mapping[class_file] = modified_file

    return modified_classes, class_file_mapping


def _run_adaptors_on_files(class_files, repo_path, adaptors, adaptors_save_path):

    for class_file in class_files:
        _run_all_adaptors_on_file(class_file, repo_path, adaptors, adaptors_save_path)


def _run_all_adaptors_on_file(class_file, repo_path, adaptors, adaptors_save_path):

    for adaptor in adaptors:
        adaptor_command = [config.TOIF_EXECUTABLE, "--adaptor", adaptor, "--housekeeping",
                           HOUSE_KEEPING_PATH, "--outputdirectory", adaptors_save_path, "--inputfile", class_file]
        logger.debug("adaptor command: %s" % adaptor_command)

        _wait_for_process_slot()
        p = subprocess.Popen(" ".join(adaptor_command), shell=True, cwd=repo_path)
        processes.append(p)


def _wait_for_process_slot():
    while len(processes) >= maximum_number_of_processes:
        _clear_processes()


def _wait_for_processes_to_finish():
    while len(processes) != 0:
        _clear_processes()


def _clear_processes():
    for process in processes:

        result = process.poll()

        if result is not None:
            processes.remove(process)

    time.sleep(0.5)
