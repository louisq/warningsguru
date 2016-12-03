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

import os
import subprocess
from shutil import copytree, rmtree

# The purpose of this utility is to prevent conflicts between commitguru and staticguru
import config
from utility.Logging import logger


def load_repository(repository_id, manager_repo_path, commit):
    # We don't need to copy the whole repository. We only need to copy .git to then extract it
    # TODO add support to load from NFS

    # for git repositories
    commitguru_repo_path = os.path.join(config.COMMITGURU_REPOSITORY_PATH, repository_id)

    commit_in_repo = is_commit_in_repository(manager_repo_path, commit)

    if not commit_in_repo:
        logger.warning("commit %s is not in repo %s. Attempting to reload repo from commitguru" % (commit, manager_repo_path))
        if os.path.exists(manager_repo_path):
            rmtree(manager_repo_path)

        copytree(commitguru_repo_path, manager_repo_path)

        commit_in_repo = is_commit_in_repository(manager_repo_path, commit)

        if not commit_in_repo:
            logger.error("Commit %s not in repository %s" % (commit, repository_id))

    return commit_in_repo


def is_commit_in_repository(repository, commit):

    if os.path.exists(repository):

        process = subprocess.Popen("git cat-file -t %s" % commit,
                                   shell=True, cwd=repository, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        # git will return "commit" if the commit hash is in the repository
        return 'commit' in process.communicate()[0]

    else:
        return False
