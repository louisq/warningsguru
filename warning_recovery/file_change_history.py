"""
The MIT License (MIT)

Copyright (c) 2017 Louis-Philippe Querel l_querel@encs.concordia.ca

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
import uuid

from repos import git
from repos.git import GIT, get_commit_modified_files
from repos.repo_manager import load_repository
from utility.commit import commit_params
from utility.service_sql import get_service_db


def get_commit_file_history(service_db, repo_id, repo_path, commit_hash, batch_run=False):

    # get list of files which have previously been analysed
    existing_files = _get_modified_files_with_history(service_db, repo_id, commit_hash)

    # get the list of files which have not previously been analysed for the commit
    files_to_analyse = filter(lambda commit_file: commit_file not in existing_files,
                              get_commit_modified_files(repo_path, commit_hash))

    commit_file_history = []
    commit_file_keys_check = {}

    if len(files_to_analyse) > 0:

        # Check out the commit if we are in a batch run where the right commit as not already been checkout
        if batch_run:
            GIT().checkout(repo_path, commit_hash)

        for file_to_analyse in files_to_analyse:

            # Confirm that the file was not deleted as part of this commit
            if not os.path.exists(os.path.join(repo_path, file_to_analyse)):
                continue

            # Get the entire commit history of the file
            commit_file_history = git.file_history(repo_path, file_to_analyse)

            # Obtain the parent of the file
            original_file = commit_file_history[len(commit_file_history) - 1]

            # Determine if the file already as a unique identifier assigned to it
            previous_file_id = _get_file_origin_id(service_db, repo_id, original_file[0], original_file[1])

            ignore_commit_files = []

            if previous_file_id:
                # If id was already assign then we should be reusing the file id
                file_id = previous_file_id
                ignore_commit_files = _get_commit_file_by_file_id(service_db, repo_id, file_id)

            elif "%s%s%s" % (original_file[0], original_file[1], None) in commit_file_keys_check.keys():
                # check if the file was analysed as part of the commit which we are presently analysing
                file_id = commit_file_keys_check["%s%s%s" % (original_file[0], original_file[1], None)]

            else:
                # if the file was never analysed we give it a new file id
                file_id = str(uuid.uuid4())

            # Converting file history of file to be saved to db into payload
            for index in xrange(len(commit_file_history)):
                file_commit = commit_file_history[index][0]
                file_commit_path = commit_file_history[index][1]

                parent_file_commit = parent_file_commit_path = None

                # if the file is not the last one then it as parents
                if index + 1 < len(commit_file_history):
                    parent_file_commit = commit_file_history[index+1][0]
                    parent_file_commit_path = commit_file_history[index+1][1]

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

    if len(commit_file_history) > 0:
        add_file_history(service_db, commit_file_history)

    processed_commit(service_db, repo_id, commit_hash, batch_run)


def _get_commits_with_no_file_history(db):
    cursor = db.get_cursor()
    query = """
            SELECT repo, commit
            FROM static_commit_processed as p, commits as c
            WHERE STATUS = 'PROCESSED'
            and file_history_processed is NULL
            and p.repo = c.repository_id and p.commit = c.commit_hash
            ORDER by author_date_unix_timestamp desc
            LIMIT 1;
            """
    cursor.execute(query)

    commit = cursor.fetchone()

    return commit if commit else None


def _get_file_origin_id(db, repo, commit_hash, file_path):
    cursor = db.get_cursor()
    query = """
            SELECT file_id
            FROM static_commit_file_history
            WHERE repo = %s and commit = %s and file_path = %s
            """

    cursor.execute(query, (repo, commit_hash, file_path))

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

    return map(lambda modified_file: modified_file[0], cursor.fetchall())


def add_file_history(db, file_history):
    cursor = db.get_cursor()
    cursor.executemany("""
    INSERT INTO static_commit_file_history
    (REPO, COMMIT, ALT_COMMIT, file_path, parent_commit, parent_file_path, file_id)
    VALUES
    (%(repo)s, %(commit)s, %(alt_commit)s, %(file_path)s, %(parent_commit)s, %(parent_file_path)s, %(file_id)s)
    """, file_history)


def processed_commit(db, repo, commit, save_transaction):
    cursor = db.get_cursor()

    cursor.execute("""
            UPDATE STATIC_COMMIT_PROCESSED
             SET file_history_processed = now()
             WHERE REPO = %s AND COMMIT = %s;
            """, (repo, commit))

    # Only commit where we know that we are not running in the pipeline. In the pipeline we need to maintain transaction
    if save_transaction:
        db.db.commit()


# Allow this script to be ran separately from the pipeline
if __name__ == "__main__":
    service_db = get_service_db()

    while True:
        commit = _get_commits_with_no_file_history(service_db)

        if not commit:
            print "no more commits to analyse"
            break
        else:
            repo_id, commit_hash, repo_path = commit_params(commit)

            load_repository(repo_id, repo_path, commit_hash)

            get_commit_file_history(service_db, repo_id, repo_path, commit_hash, batch_run=True)
