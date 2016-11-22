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
from shutil import copytree, rmtree

# The purpose of this utility is to prevent conflicts between commitguru and staticguru
import config


def load_repository(repository):
    # We don't need to copy the whole repository. We only need to copy .git to then extract it
    # TODO add support to load from NFS

    # Need a way of knowing that commitguru is not currently working on a commit.
    # 1. Use status that would prevent cg ingester from attempting to update it
    # 2. Only attempt to analyse repositories that are not being analysed.
    #     Don't want to become on the time thought

    # for git repositories
    commitguru_repo_path = os.path.join(config.COMMITGURU_REPOSITORY_PATH, repository)
    manager_repo_path = _get_manager_repository_path(repository)

    if not config.DISABLE_REPO_RESET:
        # TODO don't run the delete function every single time
        if os.path.exists(manager_repo_path):
            rmtree(manager_repo_path)

        # TODO We might not need to copy everything each time, we could just download the git repo folder
        copytree(commitguru_repo_path, manager_repo_path)


def _get_manager_repository_path(repository):
    return os.path.join(config.REPOSITORY_CACHE_PATH, repository)

