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

"""
The purpose of this script is to automatically run the TOIF adaptors on each commit that commitguru as analysed.
"""
import subprocess
import time
from time import sleep
import os

from db_versioning import flyway_runner
from pom_injector.update_pom import update_pom
from kdm_extractor import extract
from repos.repo_manager import load_repository
from repos.git import GIT
from utility.Logging import logger
from utility.service_sql import *

import config
from config import *

BUILD = "BUILD"
PROJECT_NAME = "StaticGuru"
VERSION = "0.0.1"


class AdaptorRunner:

    def __init__(self):
        logger.info("Starting %s - version %s" % (PROJECT_NAME, VERSION))

        # TODO check dependencies for all modules (toif, git, commitguru, maven, etc.)

        db = config.get_local_settings()

        # Checking the state of database and attempting to migrate if necessary
        flyway_runner.migrate_db(db[DATABASE_HOST], db[DATABASE_PORT], db[DATABASE_NAME], db[DATABASE_USERNAME], db[DATABASE_PASSWORD])

        # Once everything as been validated we can start the service
        logger.info("Service prerequisites check complete. Starting %s" % PROJECT_NAME)
        self._start_service()

    def _start_service(self):

        service_db = Service_DB(REPROCESS_FAILURES_HOURS)

        while True:
            commits = service_db.get_unprocessed_commits()

            if len(commits) > 0:

                service_db.truncate_commit_processing()
                service_db.queued_commit(commits)

                # Checkout repo to commit
                for commit in commits:
                    repo_id = commit['repo']
                    commit_hash = commit['commit']

                    service_db.processing_commit(repo_id, commit_hash)
                    repo_dir = os.path.join(config.REPOSITORY_CACHE_PATH, repo_id)

                    if not load_repository(repo_id, repo_dir, commit_hash):
                        # Failed to load the repo or the commit
                        commit_result = "COMMIT_MISSING"
                        log = "repo or commit not loaded"
                    else:

                        commit_result, log = process_inject_run_commit(commit, repo_dir)

                        if commit_result == BUILD:
                            logger.info("Build successful, now running TOIF assimilator")
                            # Build was successful so we can continue
                            log = "\n".join((log, run_assimilator(repo_dir)))

                            kdm_file = _get_kdm_file_output_path(repo_dir)
                            zip_kdm_file = kdm_file + ".zip"

                            if os.path.isfile(zip_kdm_file):

                                _extract_kdm_file(repo_dir)

                                if os.path.isfile(kdm_file):

                                    # Process extracted kdm file
                                    logger.info("Extracting warnings")
                                    warnings = extract.etl_warnings(_get_kdm_file_output_path(repo_dir), repo_dir, commit['repo'], commit['commit'])
                                    logger.info("%s warnings have been identified in commit %s" % (len(warnings), commit_hash))

                                    # Save warnings to db
                                    service_db.add_commit_warning_lines(warnings)

                                    # Get the line blames
                                    logger.info("Obtaining history of warnings")
                                    line_blames = _get_line_blames(repo_dir, warnings)

                                    for blame in line_blames:
                                        blame['repo_id'] = repo_id
                                        blame['commit_id'] = commit_hash

                                    service_db.add_commit_warning_blames(line_blames)

                                    # Get the commit parent history
                                    logger.info("Getting the commit parents")
                                    parent_commit_history = _get_commit_parents(repo_dir, repo_id)
                                    service_db.add_commit_history_graph(parent_commit_history)


                                else:
                                    log = "\n".join((log, "file %s does not exist. this is not normal as zip file existed"
                                                    % kdm_file))
                                    commit_result = "TOOL ERROR"


                            else:
                                log = "\n".join((log, "file %s does not exist. This could be normal as it is possible that"
                                                     " no files were run" % zip_kdm_file))

                    service_db.processed_commit(commit['repo'], commit['commit'], commit_result, log=log)

            else:
                logger.info("No new tasks to run. Going to sleep for %s minutes" % BACKGROUND_SLEEP_MINUTES)
                time.sleep(BACKGROUND_SLEEP_MINUTES*60)



    """
    1. get commits from commitguru that have not been ran by adaptor yet
    2. Prepare maven pom file
    """

    """
    -- static process commit table
    repo commit status build date

    -- static file warnings
    repo commit
    """

runner_base_dir_path = os.path.abspath(os.path.join(os.path.curdir, 'maven_toif_runner'))


def process_inject_run_commit(commit, repo_dir):

    logger.info("Checking out %s from %s" % (commit['commit'], repo_dir))
    subprocess.call("git reset --hard; git clean -df; git checkout %s" % commit['commit'], shell=True, cwd=repo_dir)

    # Check if it's a maven project
    pom_file_path = os.path.join(repo_dir, "pom.xml")
    pom_exists = os.path.exists(pom_file_path)

    if not pom_exists:
        logger.info("Missing POM - Nothing to build")
        return "MISSING POM", ""

    adaptor_dir_path = _get_adaptor_output_dir_path(repo_dir)

    # Attempt to update the pom file
    if not update_pom(pom_file_path, runner_base_dir_path, repo_dir, adaptor_dir_path):
        logger.error("Failed to inject staticguru in POM - Commit: %s, Repo: %s" % (commit['commit'], commit['repo']))
        return "INJECTION FAILED", ""

    # Ensure that the repository is clean
    subprocess.Popen("mvn clean:clean", shell=True, cwd=repo_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    # Create directory where to save toif adaptor files
    if not os.path.exists(adaptor_dir_path):
        os.makedirs(adaptor_dir_path)

    logger.info("Building %s and running TOIF adaptors" % commit['commit'])
    process = subprocess.Popen("mvn -T 1C package -DskipTests exec:exec", shell=True, cwd=repo_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    maven_logs = process.communicate()[0]

    if process.returncode == 0:
        logger.info("Build Success - Commit: %s" % commit['commit'])
        return BUILD, maven_logs
    else:
        logger.warning("Build Failed")
        return "FAILURE", maven_logs


def _get_adaptor_output_dir_path(repo_dir):
    return os.path.join(repo_dir, ADAPTOR_OUTPUT_DIR)


def _get_kdm_file_output_path(repo_dir):
    # TODO make this configurable
    return os.path.abspath(os.path.join(repo_dir, KDM_FILE))


def run_assimilator(repo_dir):
    adaptor_output_path = os.path.abspath(_get_adaptor_output_dir_path(repo_dir))
    assimilator_output_file_path = _get_kdm_file_output_path(repo_dir)
    # assimilator_output_file_path = "/home/louisq/test.kdm"
    assimilator_process = subprocess.Popen("%s --merge --kdmfile=%s --inputfile=%s" %
                                           (TOIF_EXECUTABLE, assimilator_output_file_path, adaptor_output_path),
                                           shell=True, cwd=os.path.abspath(repo_dir), stdout=subprocess.PIPE,
                                           stderr=subprocess.STDOUT)

    # return the assimilator log results
    sleep(20)
    return assimilator_process.communicate()[0]


def _extract_kdm_file(repo_dir):

    assimilator_output_file_path = _get_kdm_file_output_path(repo_dir)

    # TODO remove when toif is fixed and does not create two copies of the file: {name} and {name}.zip. File {name} is empty
    process = subprocess.Popen("rm %s; unzip %s" % (assimilator_output_file_path, assimilator_output_file_path + ".zip"),
                     shell=True, cwd=os.path.abspath(repo_dir), stdout=subprocess.PIPE,
                     stderr=subprocess.STDOUT)
    process.communicate()[0]
    sleep(5)


def _get_commit_parents(repo_dir, repo_id, all_commits=False):

    history = GIT().get_commit_parents(repo_dir, all_commits=all_commits)

    commit_parents = []

    for commit in history:
        for parent in commit['parents']:
            commit_parents.append({"repo_id": repo_id, "commit_id": commit["commit"], "parent_commit": parent})

    return commit_parents


def _get_line_blames(repo_dir, warnings):

    files_with_warnings = {}

    for warning in warnings:

        file_path = warning['resource']
        line_number = warning['line_number']

        if file_path not in files_with_warnings:
            files_with_warnings[file_path] = []

        if line_number not in files_with_warnings[file_path]:
            files_with_warnings[file_path].append(line_number)

    warning_lines_blames = []

    for file_path in files_with_warnings.keys():

        blames = GIT().get_warning_blames(repo_dir, file_path, files_with_warnings[file_path])
        warning_lines_blames.extend(blames)

    return warning_lines_blames

AdaptorRunner()
