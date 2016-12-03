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

# The purpose of this utility is to obtain the blames

import os
import re
import subprocess

from repos.vcs_generic import VCS
from utility.Logging import logger


class GIT (VCS):

    def checkout(self, repo_path, commit):
        logger.info("%s: Checking out commit from %s" % (commit['commit'], repo_path))
        subprocess.call("git reset --hard; git clean -df; git checkout %s" % commit['commit'], shell=True, cwd=repo_path)

    def get_current_commit_graph(self, repo_path):
        return _get_repo_dag(repo_path, only_current_commit=True)

    def get_commit_graph(self, repo_path):
        return _get_repo_dag(repo_path, only_current_commit=False)

    def get_commit_parents(self, repo_path, all_commits=False):

        if all_commits:
            git_command = "git log --pretty=format:\"%H %P\""
        else:
            git_command = "git log --pretty=format:\"%H %P\" -1"

        process = subprocess.Popen(git_command,
                                   shell=True,
                                   cwd=os.path.abspath(repo_path),
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT)
        result = process.communicate()[0]

        result = map(lambda line: _get_graph(line), result.splitlines())

        return result

    """
    This specific method will be returning the information regarding the line blame for the lines that have been provided as
    having a warning
    returns [{"origin_commit": "", 'origin_resource': "", 'origin_line': "", 'line': "", 'is_new_line': boolean}]
    """
    def get_warning_blames(self, repo_full_path, file_path, warnings):

        lines_with_blame = _get_file_blames(repo_full_path, file_path, warnings)

        # todo determine how we would handle the move or copies of lines from one file to another

        current_repo = _get_current_commit_hash(repo_full_path)[:40]

        for line in lines_with_blame:
            line['resource'] = file_path
            if line['origin_commit'] == current_repo:
                line["is_new_line"] = True
            else:
                line["is_new_line"] = False

        return lines_with_blame


# TODO remove once git functionalities are all included in this class
def _get_current_commit_hash(git_root):
    process = subprocess.Popen("git rev-parse HEAD",
                               shell=True,
                               cwd=os.path.abspath(git_root),
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)
    return process.communicate()[0]


def _generate_git_line_limit(lines):
    line_limiter = ""

    for line_number in lines:
        line_limiter += " -L %s,%s" % (line_number, line_number)

    return line_limiter


def _get_repo_dag(git_root, only_current_commit=True):
    git_command = "git log --pretty=format:\"%H %P\" %s" % ("-1" if only_current_commit else "")

    process = subprocess.Popen(git_command,
                               shell=True,
                               cwd=os.path.abspath(git_root),
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)
    result = process.communicate()[0]

    result = map(lambda line: _get_graph(line), result.splitlines())

    return result


def _get_graph(hashes):

    hashes_list = hashes.split()
    return {"commit": hashes_list[0], "parents": None if len(hashes_list) == 0 else hashes_list[1:]}


def _get_file_blames(git_root, file_path, warnings):

    # Sanitize the file path to remove leading slash
    if len(file_path) > 0 and file_path[0] == '/':
        file_path = file_path.lstrip('/')

    git_command = "git blame -lnswfMMMCCC %s %s" % (_generate_git_line_limit(warnings), file_path)

    process = subprocess.Popen(git_command,
                               shell=True,
                               cwd=os.path.abspath(git_root),
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)
    result = process.communicate()[0]

    commit_matching_pattern = re.compile(
        """
        ([\^0-9a-f]{40})\s+ # commit hash # commits with ^ appended to them are the initial commit. We would have to find out how to disable this feature
        (.+)\s+  # original file path and file name
        (\d+)\s+ # original line number
        (\d+)\)  # updated line number
        """
        , re.VERBOSE + re.IGNORECASE
    )

    lines = commit_matching_pattern.findall(result)

    commit_keys = ['origin_commit', 'origin_resource', 'origin_line', 'line']

    return [dict(zip(commit_keys, line))for line in lines]
