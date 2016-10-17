# The purpose of this utility is to obtain the blames

# git blame -p {path_to_file}
import os
import re
import subprocess



#todo List of things that would have to be completed
# Get the blame
# Take into account the dag
#
from repos.vcs_generic import VCS

"""
This specific method will be returning the information regarding the warnings that we in

git blame -lnswfMMMCCC toggles_integrated.tex


{line:#, commit_hash:""}

"""
# todo make the repo very generic so that it could eventually be extended to other VCS


class GIT (VCS):

    def get_warning_blames(self, repo_full_path, file_path, warnings):
        self.repo = repo_full_path

        lines_with_blame = _get_file_blames(repo_full_path, file_path)

        # todo determine how we would handle the move or copies of lines from one file to another

        filtered_lines = _filter_lines(lines_with_blame, warnings)

        current_repo = _get_current_commit_hash(repo_full_path)

        for line in filtered_lines:
            line['resource'] = file_path
            if line['origin_commit'] == current_repo:
                line["is_new_line"] = True
            else:
                line["is_new_line"] = False

        return filtered_lines


# TODO remove once git functionalities are all included in this class
def _get_current_commit_hash(git_root):
    process = subprocess.Popen("git rev-parse HEAD",
                               shell=True,
                               cwd=os.path.abspath(git_root),
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)
    return process.communicate()[0]


def _get_file_blames(git_root, file_path):
    process = subprocess.Popen("git blame -lnswfMMMCCC %s" % file_path,
                               shell=True,
                               cwd=os.path.abspath(git_root),
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)
    result = process.communicate()[0]

    commit_matching_pattern = re.compile(
        """
        ([0-9a-f]{40})\s # commit hash
        (.+)\s+  # original file path and file name
        (\d+)\s+ # original line number
        (\d+)\)\s # updated line number
        """
        , re.VERBOSE + re.IGNORECASE
    )

    lines = commit_matching_pattern.findall(result)

    commit_keys = ['origin_commit', 'origin_resource', 'origin_line', 'line']

    return [dict(zip(commit_keys, line))for line in lines]


def _filter_lines(lines, include):

    filtered_lines = []

    for line in lines:
        if int(line['line']) in include:
            filtered_lines.append(line)

    return filtered_lines

