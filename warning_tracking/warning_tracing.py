"""
Once we have analysed every single commit we will need to got through each commit

Get the list of all unique warnings which have been identified for the following file

Eliminate all warnings which originate after the commit was done

Obtain git blame

find all hashes which match

"""
import hashlib

from utility.file_system import get_repo_path
from utility.service_sql import get_service_db


def commit_warning_tracing():
    service_db = get_service_db()

    while True:
        commit = get_commits_with_warning_tracing(service_db)

        if not commit:
            print "no commits to analyse"
        else:
            repo_id = commit[0]
            repo_path = get_repo_path(repo_id)
            commit_hash = commit[1]



            # get the warnings for the current commit
            identified_warnings = get_commit_identified_warnings(service_db, repo_id, commit_hash)

            # get warnings for modified files which occur before and including the current commit
            print "test"

            # get the blames for the files which have warnings

            # create a hash based on the

            # determine which warnings are applicable to the current commit


    pass


def get_commits_with_warning_tracing(db):
    cursor = db.get_cursor()
    query = """
            SELECT repo, commit
            FROM static_commit_processed
            WHERE warnings_analysis_processed is NULL
            AND repo = '42e73e16-e20a-4b17-99a3-4dd7b35a6155'
            LIMIT 1;
            """
    cursor.execute(query)

    commit = cursor.fetchone()

    return commit if commit else None


def get_commit_identified_warnings(db, repo, commit):
    cursor = db.get_cursor()
    query = """
            SELECT origin_commit, origin_resource, origin_line, w.weakness, w.resource, w.line, w.sfp, w.cwe, w.generator_tool
            FROM static_commit_line_warning as w, static_commit_line_blame as b
            WHERE w.repo = %s and w.commit = %s
            and (w.repo, w.commit, w.resource, w.line) = (b.repo, b.commit, b.resource, b.line);
            """
    cursor.execute(query, (repo, commit))

    warning_rows = cursor.fetchall()

    warnings = {}

    for warning in warning_rows:
        key = hashlib.sha224("%s%s%s%s" % (warning[0], warning[1], warning[2], warning[3])).hexdigest()
        warnings[key] = {
            "origin_commit": warning[0],
            "origin_resource": warning[1],
            "origin_line": warning[2],
            "weakness": warning[3],
            "repo": repo,
            "commit": commit,
            "resource": warning[4],
            "line": warning[5],
            "sfp": warning[6],
            "cwe": warning[7],
            "generator_tool": warning[8]
        }

    return warnings


def recover_warnings(db, repo, commit):
    cursor = db.get_cursor()
    query = """
            SELECT origin_commit, origin_resource, origin_line, w.weakness, w.resource, w.line, w.sfp, w.cwe, w.generator_tool
            FROM static_commit_line_warning as w, static_commit_line_blame as b
            WHERE w.repo = %s and w.commit = %s
            and (w.repo, w.commit, w.resource, w.line) = (b.repo, b.commit, b.resource, b.line);


            select DISTINCT (origin_commit, origin_resource, origin_line, weakness)
            FROM static_commit_line_warning as w, static_commit_line_blame as b, static_commit_file_history as h
            where h.file_id in (SELECT distinct(file_id) from static_commit_file_history where repo = {repo} and commit = {commit})
            and (w.repo, w.commit, w.resource, w.line) = (b.repo, b.commit, b.resource, b.line)
            and (w.repo, w.commit) = (h.repo, w.commit) and w.repo = {repo} and w.commit = {commit};
            """
    cursor.execute(query, (repo, commit))

    warning_rows = cursor.fetchall()

    warnings = {}

    for warning in warning_rows:
        key = hashlib.sha224("%s%s%s%s" % (warning[0], warning[1], warning[2], warning[3])).hexdigest()
        warnings[key] = {
            "origin_commit": warning[0],
            "origin_resource": warning[1],
            "origin_line": warning[2],
            "weakness": warning[3],
            "repo": repo,
            "commit": commit,
            "resource": warning[4],
            "line": warning[5],
            "sfp": warning[6],
            "cwe": warning[7],
            "generator_tool": warning[8]
        }

    return warnings

def processed_commit(db, repo, commit):
    cursor = db.get_cursor()

    cursor.execute("""
            UPDATE STATIC_COMMIT_PROCESSED
             SET warnings_analysis_processed = now()
             WHERE REPO = %s AND COMMIT = %s;
            """, (repo, commit))
    db.db.commit()

commit_warning_tracing()

