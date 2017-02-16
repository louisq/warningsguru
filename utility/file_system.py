import os

from config import REPOSITORY_CACHE_PATH


def get_repo_path(repo):
    return os.path.join(REPOSITORY_CACHE_PATH, repo)
