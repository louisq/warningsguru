import fnmatch
import os
import re
import time
import subprocess

import config

maximum_number_of_processes = 48
processes = []

HOUSE_KEEPING_PATH = os.path.abspath("HouseKeeping.txt")


def run(repo_path, adaptor_save_path):

    list_of_allowed_extensions = ['java']
    adaptors_for_java = ["Findbugs", "Jlint"]

    # identified modified files
    modified_files = _identify_modified_files(repo_path)

    # filter modified files to only have java files

    filtered_modified_files = _filter_files(modified_files, list_of_allowed_extensions)

    compiled_files = _get_all_class_file(repo_path)

    modified_class_files = _identify_modified_class_files(filtered_modified_files, compiled_files)

    _run_adaptors_on_files(modified_class_files, repo_path, adaptors_for_java, adaptor_save_path)


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


def _identify_modified_class_files(modified_files, classes):

    modified_classes = []

    for modified_file in modified_files:
        split_name = modified_file.split("/")
        name = split_name[len(split_name)-1].split(".")[0]

        if name not in classes:
            pass

        classes = classes.get(name)

        if len(classes) > 1:
            pass

        modified_classes += classes[classes.keys()[0]]

    return modified_classes


def _run_adaptors_on_files(class_files, repo_path, adaptors, adaptors_save_path):

    for class_file in class_files:
        _run_all_adaptors_on_file(class_file, repo_path, adaptors, adaptors_save_path)


def _run_all_adaptors_on_file(class_file, repo_path, adaptors, adaptors_save_path):

    for adaptor in adaptors:
        adaptor_command = [config.TOIF_EXECUTABLE, "--adaptor", adaptor, "--housekeeping",
                           HOUSE_KEEPING_PATH, "--outputdirectory", adaptors_save_path, "--inputfile", class_file]
        print adaptor_command

        _wait_for_process_slot()
        p = subprocess.Popen(adaptor_command, shell=False, cwd=repo_path)
        processes.append(p)


def _wait_for_process_slot():
    while len(processes) >= maximum_number_of_processes:
        for process in processes:

            if process.poll():
                processes.remove(process)

    time.sleep(0.5)
