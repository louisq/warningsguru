"""
Once we have analysed every single commit we will need to got through each commit

Get the list of all unique warnings which have been identified for the following file

Eliminate all warnings which originate after the commit was done

Obtain git blame

find all hashes which match

"""
import hashlib
import os

from repos.git import GIT, _get_file_blames
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

            modified_files = get_modified_files(service_db, repo_id, commit_hash)

            if len(modified_files.keys()) == 0:
                print "no modified files in commit %s" % commit_hash
                continue

            # get the warnings for the current commit
            identified_warnings = get_commit_identified_warnings(service_db, repo_id, commit_hash)

            # get warnings for modified files which occur before and including the current commit
            recovered_warnings = recover_warnings(service_db, repo_id, commit_hash)

            double_check = []
            double_check_count = 0

            for identified_warning in identified_warnings:
                for warning_id in identified_warnings[identified_warning]:
                    warning = identified_warnings[identified_warning][warning_id]
                    file_path = warning['resource'][1:]
                    if file_path not in modified_files:
                        continue
                    file_id = modified_files[file_path]
                    if file_id not in double_check:
                        double_check.append(file_id)



            GIT().checkout(repo_path, commit_hash)

            confirmed_recovered_warnings = []
            warning_lines = 0

            for file_path in filter(lambda f: modified_files[f] in recovered_warnings, modified_files.keys()):
                if not os.path.exists(os.path.join(repo_path, file_path)):
                    continue

                file_id = modified_files[file_path]
                possible_file_warnings = recovered_warnings[file_id]

                file_origin = get_file_origin_keys(repo_path, file_path)
                file_origin_keys = file_origin.keys()

                found_warnings = filter(lambda warning_key: warning_key in file_origin_keys, possible_file_warnings)

                if len(found_warnings) > 0:
                    for origin_line in found_warnings:
                        warning_lines += 1
                        for line_warning in possible_file_warnings[origin_line]:
                            warning_obj = possible_file_warnings[origin_line][line_warning]

                            recovered_warning = True
                            if origin_line in identified_warnings and line_warning in identified_warnings[origin_line]:
                                recovered_warning = False

                            new_warning = False
                            # todo match line to commit

                            confirmed_recovered_warnings.append(
                                {"repo": repo_id, "commit": commit_hash, "file_path": file_path,
                                 "line": file_origin[origin_line], "origin_commit": warning_obj['origin_commit'],
                                 "origin_file_path": warning_obj['origin_resource'],
                                 "origin_line": warning_obj['origin_line'],

                                 "file_id": file_id, "new_warning": new_warning, "recovered_warning": recovered_warning}
                            )

                            """  REPO TEXT not null,
  COMMIT TEXT not null,
  FILE_PATH TEXT not null,
  LINE TEXT not null,
  ORIGIN_COMMIT TEXT not null,
  ORIGIN_FILE_PATH TEXT not null,
  ORIGIN_LINE TEXT not null,
  WEAKNESS TEXT not null,
  SFP TEXT not null,
  CWE TEXT not null,
  GENERATOR_TOOL TEXT not null,
  FILE_ID TEXT not null,
  NEW_WARNING BOOLEAN not null,
  RECOVERED_WARNING BOOLEAN not null,"""

                            print "hello"

                    print "success"
                print "test"
                # def _get_file_blames(git_root, file_path, lines)

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
        line_key = hashlib.sha224("%s%s%s" % (warning[0], warning[1], warning[2])).hexdigest()

        if line_key not in warnings:
            warnings[line_key] = {}

        warning_key = hashlib.sha224("%s%s%s%s" % (warning[0], warning[1], warning[2], warning[3])).hexdigest()
        warnings[line_key][warning_key] = {
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


def get_file_origin_keys(repo_path, file_path):
    result = {}

    for line in _get_file_blames(repo_path, file_path, []):
        result[hashlib.sha224(
            "%s%s%s" % (line["origin_commit"], line["origin_resource"], line["origin_line"])).hexdigest()] = line[
            "line"]

    return result


def recover_warnings(db, repo, commit):
    cursor = db.get_cursor()
    query = """
            SELECT distinct(file_id, origin_commit, origin_resource, origin_line, weakness),
            file_id, origin_commit, origin_resource, origin_line, weakness
            from static_commit_file_history as h
            join static_commit_line_blame as b on (h.repo, h.commit, h.file_path) = (b.repo, b.origin_commit, b.origin_resource)
            join static_commit_line_warning as w on (b.repo, b.commit, b.resource, b.line) = (w.repo, w.commit, w.resource, w.line)
            where h.file_id in (SELECT file_id from static_commit_file_history where repo =  %s and commit = %s group by file_id)
            UNION
            SELECT distinct(file_id, origin_commit, origin_resource, origin_line, weakness),
            file_id, origin_commit, origin_resource, origin_line, weakness
            from static_commit_file_history as h
            join static_commit_line_blame as b on (h.repo, h.alt_commit, h.file_path) = (b.repo, b.origin_commit, b.origin_resource)
            join static_commit_line_warning as w on (b.repo, b.commit, b.resource, b.line) = (w.repo, w.commit, w.resource, w.line)
            where h.file_id in (SELECT file_id from static_commit_file_history where repo =  %s and commit = %s group by file_id);

            """
    cursor.execute(query, (repo, commit, repo, commit))

    warning_rows = cursor.fetchall()

    warnings = {}

    for warning in warning_rows:
        file_id = warning[1]
        if file_id not in warnings:
            warnings[file_id] = {}

        line_key = hashlib.sha224("%s%s%s" % (warning[2], warning[3], warning[4])).hexdigest()
        if line_key not in warnings[file_id]:
            warnings[file_id][line_key] = {}

        warning_key = hashlib.sha224("%s%s%s%s" % (warning[2], warning[3], warning[4], warning[5])).hexdigest()

        if warning_key in warnings[file_id][line_key]:
            print "fail"
        warnings[file_id][line_key][warning_key] = {
            "file_id": warning[1],
            "origin_commit": warning[2],
            "origin_resource": warning[3],
            "origin_line": warning[4],
            "weakness": warning[5]
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


def get_modified_files(db, repo, commit):
    cursor = db.get_cursor()
    query = """
                SELECT file_id, file_path
                from static_commit_file_history
                where repo = %s and commit = %s
                group by file_id, file_path;
                """
    cursor.execute(query, (repo, commit))

    files = cursor.fetchall()

    file_map = {}
    for f in files:
        file_map[f[1]] = f[0]

    return file_map


commit_warning_tracing()

"""


SELECT distinct(file_id, origin_commit, origin_resource, origin_line, weakness), file_id, h.repo, origin_commit, origin_resource, origin_line, w.weakness
from static_commit_file_history as h, static_commit_line_blame as b, static_commit_line_warning as w
where h.file_id in (SELECT file_id from static_commit_file_history where repo = '42e73e16-e20a-4b17-99a3-4dd7b35a6155' and commit = 'a9a8957425b85b70441b15124bba25bf183868c3' group by file_id)
and (h.repo, h.alt_commit, h.file_path) = (b.repo, b.origin_commit, b.origin_resource)
and (b.repo, b.commit, b.resource, b.line) = (w.repo, w.commit, w.resource, w.line);


select distinct(hh.origin_commit, hh.origin_resource, hh.origin_line, w.weakness)
from static_commit_line_warning as w, static_commit_line_blame as b,
(SELECT distinct(file_id, origin_commit, origin_resource, origin_line), file_id, h.repo, origin_commit, origin_resource, origin_line
from static_commit_file_history as h, static_commit_line_blame as b
where h.file_id in (SELECT file_id from static_commit_file_history where repo = '42e73e16-e20a-4b17-99a3-4dd7b35a6155' and commit = 'a9a8957425b85b70441b15124bba25bf183868c3' group by file_id)
and (h.repo = b.repo) and (h.alt_commit = b.origin_commit) and(h.file_path = b.origin_resource)) as hh
where (w.repo, w.commit, w.resource, w.line) = (b.repo, b.commit, b.resource, b.line)
and (b.repo, b.origin_commit, b.origin_resource, b.origin_line) = (hh.repo, hh.origin_commit, hh.origin_resource, hh.origin_line);

select distinct(hh.origin_commit, hh.origin_resource, hh.origin_line, w.weakness)
from static_commit_line_warning as w, static_commit_line_blame as b,
(SELECT distinct(file_id, origin_commit, origin_resource, origin_line), file_id, h.repo, origin_commit, origin_resource, origin_line
from static_commit_file_history as h, static_commit_line_blame as b
where h.file_id in (SELECT file_id from static_commit_file_history where repo = '42e73e16-e20a-4b17-99a3-4dd7b35a6155' and commit = 'a9a8957425b85b70441b15124bba25bf183868c3' group by file_id)
and (h.repo = b.repo) and (h.commit = b.origin_commit) and(h.file_path = b.origin_resource)) as hh
where (w.repo, w.commit, w.resource, w.line) = (b.repo, b.commit, b.resource, b.line)
and (b.repo, b.origin_commit, b.origin_resource, b.origin_line) = (hh.repo, hh.origin_commit, hh.origin_resource, hh.origin_line);

"""
