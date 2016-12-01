import os
import subprocess
from shutil import copytree, rmtree

# The purpose of this utility is to prevent conflicts between commitguru and staticguru
import config


def load_repository(repository_id, manager_repo_path, commit):
    # We don't need to copy the whole repository. We only need to copy .git to then extract it
    # TODO add support to load from NFS

    # for git repositories
    commitguru_repo_path = os.path.join(config.COMMITGURU_REPOSITORY_PATH, repository_id)

    commit_in_repo = is_commit_in_repository(manager_repo_path, commit)

    if not commit_in_repo:
        print "commit %s is not in repo %s. Attempting to reload repo from commitguru" % (commit, manager_repo_path)
        if os.path.exists(manager_repo_path):
            rmtree(manager_repo_path)

        copytree(commitguru_repo_path, manager_repo_path)

        commit_in_repo = is_commit_in_repository(manager_repo_path, commit)

        if not commit_in_repo:
            print "Commit %s not in repo" % commit

    return commit_in_repo


def is_commit_in_repository(repository, commit):

    if os.path.exists(repository):

        process = subprocess.Popen("git cat-file -t %s" % commit,
                                   shell=True, cwd=repository, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        # git will return "commit" if the commit hash is in the repository
        return 'commit' in process.communicate()[0]

    else:
        return False
