import os
import uuid

from repos import git
from repos.git import GIT, _commit_modified_files, _follow_file_history
from repos.repo_manager import load_repository
from utility.file_system import get_repo_path
from utility.service_sql import get_service_db


def get_commit_file_history():
    service_db = get_service_db()

    while (True):
        commit = _get_commits_with_no_file_history(service_db)

        if not commit:
            print "no more commits to analyse"
            break
        else:

            repo_id = commit[0]
            repo_path = get_repo_path(repo_id)
            commit_hash = commit[1]

            load_repository(repo_id, repo_path, commit_hash)

            # get list of files which have previously been analysed
            existing_files = _get_modified_files_with_history(service_db, repo_id, commit_hash)

            # get the list of modified files in the commit
            commit_modified_files = _commit_modified_files(repo_path, commit_hash)

            files_to_analyse = filter(lambda commit_file: commit_file not in existing_files, commit_modified_files)

            commit_file_history = []
            commit_file_keys_check = {}

            if len(files_to_analyse) > 0:
                GIT().checkout(repo_path, commit_hash)

                for commit_file in files_to_analyse:

                    if not os.path.exists(os.path.join(repo_path, commit_file)):
                        continue

                    history = git.file_history(repo_path, commit_file)

                    first_file = history[len(history) - 1]

                    # if first_file[1] == "phoenix-core/src/main/java/org/apache/phoenix/expression/function/ByteBasedRegexpSplitFunction.java":
                    #     print str(history)

                    previous_file_id = _get_file_origin_id(service_db, repo_id, first_file[0], first_file[1])

                    ignore_commit_files = []

                    if previous_file_id:
                        file_id = previous_file_id
                        ignore_commit_files = _get_commit_file_by_file_id(service_db, repo_id, file_id)
                        print "pre"

                    # check if the file was analysed in the commit
                    elif "%s%s%s" % (first_file[0], first_file[1], None) in commit_file_keys_check.keys():
                        file_id = commit_file_keys_check["%s%s%s" % (first_file[0], first_file[1], None)]
                    else:
                        file_id = str(uuid.uuid4())

                    # Get the list of to determine which ones have not previously been run

                    for index in xrange(len(history)):
                        file_commit = history[index][0]
                        file_commit_path = history[index][1]

                        parent_file_commit = parent_file_commit_path = None

                        if index + 1 < len(history):
                            parent_file_commit = history[index+1][0]
                            parent_file_commit_path = history[index+1][1]

                        commit_file_key = "%s%s%s" % (file_commit, file_commit_path, parent_file_commit)
                        if commit_file_key not in ignore_commit_files and commit_file_key not in commit_file_keys_check.keys():

                            commit_file_keys_check[commit_file_key] = file_id
                            commit_file_history.append(
                                {
                                    "repo": repo_id,
                                    "commit": file_commit,
                                    "alt_commit": "^%s" % file_commit[:39],
                                    "file_path": file_commit_path,
                                    "parent_commit": parent_file_commit,
                                    "parent_file_path": parent_file_commit_path,
                                    "file_id": file_id
                                }
                            )


                    # todo need to be able to do this incrementally for new commits

            if len(commit_file_history) > 0:
                add_file_history(service_db, commit_file_history)

            processed_commit(service_db, repo_id, commit_hash)


def _get_commits_with_no_file_history(db):
    cursor = db.get_cursor()
    query = """
            SELECT repo, commit
            FROM static_commit_processed as p, commits as c
            WHERE file_history_processed is NULL
            and p.repo = c.repository_id and p.commit = c.commit_hash
            AND repo = '55a40844-8e8a-4910-9e2a-47b2caf478dc'
            ORDER by author_date_unix_timestamp desc
            LIMIT 1;
            """
    cursor.execute(query)

    commit = cursor.fetchone()

    return commit if commit else None


def _get_file_origin_id(db, repo, commit, file_path):
    cursor = db.get_cursor()
    query = """
            SELECT file_id
            FROM static_commit_file_history
            WHERE repo = %s and commit = %s and file_path = %s
            """

    cursor.execute(query, (repo, commit, file_path))

    commit = cursor.fetchone()

    return commit[0] if commit else None


def _get_commit_file_by_file_id(db, repo, file_id):
    cursor = db.get_cursor()
    query = """
                SELECT commit, file_path, parent_commit
                FROM static_commit_file_history
                WHERE repo = %s and file_id = %s
                """

    cursor.execute(query, (repo, file_id))

    commit = cursor.fetchall()

    return map(lambda f: '%s%s%s' % (f[0], f[1], f[2]), commit) if commit else []


def _get_modified_files_with_history(db, repo, commit):
    cursor = db.get_cursor()
    query = """
            SELECT file_path
            FROM static_commit_file_history
            WHERE repo = %s and commit = %s
            """

    cursor.execute(query, (repo, commit))

    return map(lambda file: file[0], cursor.fetchall())


def add_file_history(db, file_history):
    cursor = db.get_cursor()
    cursor.executemany("""
    INSERT INTO static_commit_file_history
    (REPO, COMMIT, ALT_COMMIT, file_path, parent_commit, parent_file_path, file_id)
    VALUES
    (%(repo)s, %(commit)s, %(alt_commit)s, %(file_path)s, %(parent_commit)s, %(parent_file_path)s, %(file_id)s)
    """, file_history)

def processed_commit(db, repo, commit):
    cursor = db.get_cursor()

    cursor.execute("""
            UPDATE STATIC_COMMIT_PROCESSED
             SET file_history_processed = now()
             WHERE REPO = %s AND COMMIT = %s;
            """, (repo, commit))
    db.db.commit()

get_commit_file_history()
