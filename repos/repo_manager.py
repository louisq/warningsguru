import os
from shutil import copytree, rmtree

# The purpose of this utility is to prevent conflicts between commitguru and staticguru
from toif.commitguru import config


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

    # TODO don't run the delete function every single time
    rmtree(manager_repo_path)

    # TODO We might not need to copy everything each time
    copytree(commitguru_repo_path, manager_repo_path)


def _get_manager_repository_path(repository):
    return os.path.join(config.REPOSITORY_CACHE_PATH, repository)

