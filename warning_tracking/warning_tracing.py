"""
Once we have analysed every single commit we will need to got through each commit

Get the list of all unique warnings which have been identified for the following file

Eliminate all warnings which originate after the commit was done

Obtain git blame

find all hashes which match

"""
import hashlib
import os

import time
from psycopg2._psycopg import IntegrityError

from repos.git import GIT, _get_file_blames
from utility.file_system import get_repo_path
from utility.service_sql import get_service_db


def commit_warning_tracing():
    service_db = get_service_db()

    while True:
        commit = get_commits_with_no_warning_tracing(service_db)

        if not commit:
            print "no commits to analyse"
            time.sleep(15*60)
        else:
            repo_id = commit[0]
            repo_path = get_repo_path(repo_id)
            commit_hash = commit[1]
            processing_commit(service_db, repo_id, commit_hash)
            delete_previously_recovered_commit_warnings(service_db, repo_id, commit_hash)

            modified_files = get_modified_files(service_db, repo_id, commit_hash)

            print "Analysing repo:%s commit: %s - files: %s" % (repo_id, commit_hash, len(modified_files))

            if len(modified_files.keys()) == 0:
                print "no modified files in commit %s" % commit_hash
                continue

            # get the warnings for the current commit
            identified_warnings = get_commit_identified_warnings(service_db, repo_id, commit_hash)
            identified_warnings_count = 0
            for iw in identified_warnings:
                for iww in identified_warnings[iw]:
                    identified_warnings_count += 1


            # get warnings for modified files which occur before and including the current commit
            recovered_warnings = recover_warnings(service_db, repo_id, commit_hash)

            double_check_count = 0

            GIT().checkout(repo_path, commit_hash)

            confirmed_recovered_warnings = []
            warning_lines = 0

            files_with_warnings = filter(lambda f: modified_files[f] in recovered_warnings, modified_files.keys())
            for file_path in files_with_warnings:
                if not os.path.exists(os.path.join(repo_path, file_path)):
                    continue

                file_id = modified_files[file_path]
                possible_file_warnings = recovered_warnings[file_id]

                file_origin = get_file_origin_keys(repo_path, file_path)
                file_origin_keys = file_origin.keys()

                found_warnings = filter(lambda warning_key: warning_key in file_origin_keys, possible_file_warnings.keys())

                if len(found_warnings) > 0:
                    for origin_line in found_warnings:
                        warning_lines += 1
                        for line_warning in possible_file_warnings[origin_line]:
                            warning_obj = possible_file_warnings[origin_line][line_warning]

                            recovered_warning = not (origin_line in identified_warnings and line_warning in identified_warnings[origin_line])

                            if not recovered_warning:
                                double_check_count += 1

                            new_warning = warning_obj['origin_commit'].replace("^", "") in commit_hash

                            confirmed_recovered_warnings.append(
                                {"repo": repo_id, "commit": commit_hash, "file_path": file_path,
                                 "line": file_origin[origin_line], "origin_commit": warning_obj['origin_commit'],
                                 "origin_file_path": warning_obj['origin_resource'],
                                 "origin_line": warning_obj['origin_line'], "weakness": warning_obj['weakness'],
                                 "sfp": warning_obj['sfp'], "cwe": warning_obj['cwe'],
                                 "generator_tool": warning_obj['generator_tool'], "file_id": file_id,
                                 "new_warning": new_warning, "recovered_warning": recovered_warning}
                            )

            print "Finished analysing commit"

            print "Recovered %s warnings where sg found %s. %s of these were in recovered" % (len(confirmed_recovered_warnings), identified_warnings_count, double_check_count)
            # get the blames for the files which have warnings

            try:
                add_recovered_warnings(service_db, confirmed_recovered_warnings)
                processed_commit(service_db, repo_id, commit_hash)
            except IntegrityError as e:
                print "conflict arose. Continuing"
                service_db = get_service_db()
                continue
            print ""


def get_commits_with_no_warning_tracing(db):
    cursor = db.get_cursor()
    query = """
            SELECT repo, commit
            FROM static_commit_processed
            WHERE warnings_analysis_processed is NULL
            and (warnings_analysis_processing is null or warnings_analysis_processing < NOW() - INTERVAL '2 hour')
            AND repo = 'b811c1aa-4065-44a6-a69c-c76ed821392c'
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

        origin_commit = warning[0].strip()
        origin_resource = warning[1].strip()
        origin_line = warning[2]
        weakness = warning[3].strip()

        line_key = hashlib.sha224("%s%s%s" % (origin_commit, origin_resource, origin_line)).hexdigest()
        if line_key not in warnings:
            warnings[line_key] = {}

        warning_key = hashlib.sha224("%s%s%s%s" % (origin_commit, origin_resource, origin_line, weakness)).hexdigest()
        warnings[line_key][warning_key] = {
            "origin_commit": warning[0],
            "origin_resource": warning[1],
            "origin_line": warning[2],
            "weakness": weakness,
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
            "%s%s%s" % (line["origin_commit"].strip(), line["origin_resource"].strip(), line["origin_line"])).hexdigest()] = line[
            "line"]

    return result


def recover_warnings(db, repo, commit):
    cursor = db.get_cursor()
    query = """
            SELECT distinct(file_id, origin_commit, origin_resource, origin_line, weakness),
            file_id, origin_commit, origin_resource, origin_line, weakness, sfp, cwe, generator_tool
            from static_commit_file_history as h
            join static_commit_line_blame as b on (h.repo, h.commit, h.file_path) = (b.repo, b.origin_commit, b.origin_resource)
            join static_commit_line_warning as w on (b.repo, b.commit, b.resource, b.line) = (w.repo, w.commit, w.resource, w.line)
            where h.file_id in (SELECT file_id from static_commit_file_history where repo =  %s and commit = %s group by file_id)
            UNION
            SELECT distinct(file_id, origin_commit, origin_resource, origin_line, weakness),
            file_id, origin_commit, origin_resource, origin_line, weakness, sfp, cwe, generator_tool
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

        line_key = hashlib.sha224("%s%s%s" % (warning[2].strip(), warning[3].strip(), warning[4])).hexdigest()
        if line_key not in warnings[file_id]:
            warnings[file_id][line_key] = {}

        warning_key = hashlib.sha224("%s%s%s%s" % (warning[2].strip(), warning[3].strip(), warning[4], warning[5].strip())).hexdigest()

        if warning_key in warnings[file_id][line_key]:
            print "fail"
        warnings[file_id][line_key][warning_key] = {
            "file_id": warning[1],
            "origin_commit": warning[2],
            "origin_resource": warning[3],
            "origin_line": warning[4],
            "weakness": warning[5],
            "sfp": warning[6],
            "cwe": warning[7],
            "generator_tool": warning[8]
        }

    return warnings


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


def processing_commit(db, repo, commit):
    cursor = db.get_cursor()

    cursor.execute("""
                UPDATE STATIC_COMMIT_PROCESSED
                 SET warnings_analysis_processing = now()
                 WHERE REPO = %s AND COMMIT = %s;
                """, (repo, commit))
    db.db.commit()


def delete_previously_recovered_commit_warnings(db, repo, commit):
    cursor = db.get_cursor()

    cursor.execute("""
                    DELETE FROM STATIC_COMMIT_WARNINGS_PROCESSED
                     WHERE REPO = %s AND COMMIT = %s;
                    """, (repo, commit))


def add_recovered_warnings(db, recovered_warnings):
    cursor = db.get_cursor()
    cursor.executemany("""
    INSERT INTO static_commit_warnings_processed
    (REPO, COMMIT, FILE_PATH, LINE, ORIGIN_COMMIT, ORIGIN_FILE_PATH, ORIGIN_LINE, WEAKNESS, SFP, CWE, GENERATOR_TOOL, FILE_ID, NEW_WARNING, RECOVERED_WARNING)
    VALUES
    (%(repo)s, %(commit)s, %(file_path)s, %(line)s, %(origin_commit)s, %(origin_file_path)s, %(origin_line)s, %(weakness)s, %(sfp)s, %(cwe)s, %(generator_tool)s, %(file_id)s, %(new_warning)s, %(recovered_warning)s)
    """, recovered_warnings)


def processed_commit(db, repo, commit):
    cursor = db.get_cursor()

    cursor.execute("""
            UPDATE STATIC_COMMIT_PROCESSED
             SET warnings_analysis_processed = now()
             WHERE REPO = %s AND COMMIT = %s;
            """, (repo, commit))
    db.db.commit()


commit_warning_tracing()
