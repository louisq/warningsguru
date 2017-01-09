"""
The MIT License (MIT)

Copyright (c) 2016-2017 Louis-Philippe Querel l_querel@encs.concordia.ca

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
from static_analysis_runner.post_build_runner import run
import subprocess
import time

from db_versioning import flyway_runner
from kdm_extractor import extract
from repos.repo_manager import load_repository
from repos.git import GIT
from utility.artifact_archiver import archive, artifact_archiver_version
from utility.jdk_override import JdkOverride
from utility.mvn_override import MvnOverride
from utility.service_sql import *

import config
from config import *

"""
The purpose of this script is to automatically run the TOIF adaptors on each commit that commitguru as analysed.
"""
PROJECT_NAME = "StaticGuru"
VERSION = "0.1.2"

BUILD_SUCCESS = "BUILD"
BUILD_FAILED = "FAILURE"


class StaticGuruService:

    def __init__(self):
        logger.info("Starting %s - version %s" % (PROJECT_NAME, VERSION))

        # TODO check dependencies for all modules (toif, git, commitguru, maven, etc.)

        db = config.get_local_settings()

        # Checking the state of database and attempting to migrate if necessary
        flyway_runner.migrate_db(db[DATABASE_HOST], db[DATABASE_PORT], db[DATABASE_NAME], db[DATABASE_USERNAME], db[DATABASE_PASSWORD])

        # Load overrides
        self._jdk_override_loader()
        self._maven_override_loader()

        # Once everything as been validated we can start the service
        logger.info("Service prerequisites check complete. Starting %s" % PROJECT_NAME)
        self._start_service()

    def _jdk_override_loader(self):
        self.jdk_override = self.__generic_override_loader("JDK", JdkOverride)

    def _maven_override_loader(self):
        self.mvn_override = self.__generic_override_loader("MVN", MvnOverride)

    def __generic_override_loader(self, conf_variable, override_class):

        if "OVERRIDES" in dir(config) and isinstance(config.OVERRIDES, dict):
            if conf_variable in OVERRIDES and isinstance(OVERRIDES[conf_variable], list):
                override = override_class(OVERRIDES[conf_variable])
                logger.info("Loaded the following %s overrides %s" % (override.name, str(override.overrides)))
                return override
            else:
                logger.warn("%s is missing from OVERRIDES in config file" % conf_variable)
                return override_class([])
        else:
            logger.warn("OVERRIDES is missing from config file")
            return override_class([])

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

                        commit_result, log = self.checkout_and_build_commit(commit, repo_dir)

                        # We run static analysis even if the build as failed as a project is usually composed of sub
                        # projects and we might be able to recover some of the warnings
                        if commit_result in [BUILD_SUCCESS, BUILD_FAILED]:

                            # Run static analysis on the generated, modified class files
                            logger.info("%s: Running static analysis" % commit_hash)
                            class_file_mapping = _run_static_analysis(repo_dir, commit_hash)

                            if len(class_file_mapping) > 0:
                                logger.info("%s: Running TOIF file warnings assimilator" % commit_hash)
                                # Build was successful so we can continue
                                log = "\n".join((log, run_assimilator(repo_dir)))

                                logger.info("%s: Attempting to extract file warnings from assimilator" % commit_hash)
                                _manage_assimilator_result(repo_dir, commit, service_db, class_file_mapping)

                            else:
                                logger.info("%s: No TOIF file warnings to assimilate" % commit_hash)

                        if ARTIFACT_ARCHIVER:
                            if ARTIFACT_ARCHIVER_PATH:
                                logger.info("%s: Running archiving on build artifacts as enabled" % commit_hash)
                                archiving_result = archive(repo_dir, ARTIFACT_ARCHIVER_PATH, repo_id, commit_hash)
                                if archiving_result:
                                    service_db.commit_log_tool(repo_id, commit_hash, 'artifacts_archived', artifact_archiver_version)
                                    logger.info("%s: Finished archiving of build artifacts" % commit_hash)
                            else:
                                logger.warn("Build artifact archiving cannot be enabled if the archiving path is not specified")

                    # Get the commit parent history
                    logger.info("%s: Saving the commit parents" % commit_hash)
                    parent_commit_history = _get_commit_parents(repo_dir, repo_id)
                    service_db.add_commit_history_graph(parent_commit_history)

                    service_db.processed_commit(commit['repo'], commit['commit'], commit_result, log=log)

            else:
                logger.info("No new tasks to run. Going to sleep for %s minutes" % BACKGROUND_SLEEP_MINUTES)
                time.sleep(BACKGROUND_SLEEP_MINUTES*60)

    def checkout_and_build_commit(self, commit, repo_dir):

        commit_hash = commit['commit']
        logger.info("%s: Checking out commit from %s" % (commit_hash, repo_dir))
        git_reset_process = subprocess.Popen("git reset --hard; git clean -df; git checkout %s" % commit_hash,
                                             shell=True, cwd=repo_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logger.info("%s: %s" % (commit_hash, "".join(map(str, git_reset_process.communicate()))))

        # Check if it's a maven project
        pom_file_path = os.path.join(repo_dir, "pom.xml")
        pom_exists = os.path.exists(pom_file_path)

        if not pom_exists:
            logger.info("%s: Missing POM - Nothing to build" % commit_hash)
            return "MISSING POM", ""

        # Determine if we need to override the jdk
        author_date = commit['author_date'].date()
        jdk_value = self.jdk_override.get_override(commit_hash, author_date)
        mvn_value = self.mvn_override.get_override(commit_hash, author_date)

        logger.info("%s: Building commit using MAVEN" % commit_hash)
        # run the commit build
        mvn_command = "{jdk} MAVEN_OPTS=\"{maven_options}\" {mvn} clean package -DskipTests"\
            .format(jdk=jdk_value, maven_options=MAVEN_OPTS, mvn=mvn_value)

        logger.debug("%s: Maven command '%s'" % (commit_hash, mvn_command))

        mvn_process = subprocess.Popen(mvn_command, shell=True, cwd=repo_dir, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
        maven_logs = mvn_process.communicate()[0]

        if mvn_process.returncode == 0:
            logger.info("%s: Build Success" % commit_hash)
            return BUILD_SUCCESS, maven_logs
        else:
            logger.warning("%s: Build Failed" % commit_hash)
            return BUILD_FAILED, maven_logs


def _get_adaptor_output_dir_path(repo_dir):
    return os.path.join(repo_dir, ADAPTOR_OUTPUT_DIR)


def _get_kdm_file_output_path(repo_dir):
    # TODO make this configurable
    return os.path.abspath(os.path.join(repo_dir, KDM_FILE))


def _run_static_analysis(repo_dir, commit):
    adaptor_dir_path = _get_adaptor_output_dir_path(repo_dir)

    # Create directory where to save toif adaptor files
    if not os.path.exists(adaptor_dir_path):
        os.makedirs(adaptor_dir_path)
    return run(repo_dir, adaptor_dir_path, commit)


def _manage_assimilator_result(repo_dir, commit, service_db, class_file_mapping):
    kdm_file = _get_kdm_file_output_path(repo_dir)
    zip_kdm_file = kdm_file + ".zip"
    repo_id = commit['repo']
    commit_hash = commit['commit']

    # Determine if assimilator generated kdm file
    if os.path.isfile(zip_kdm_file):

        _extract_kdm_file(repo_dir)

        if os.path.isfile(kdm_file):

            # Process extracted kdm file
            logger.info("%s: Extracting warnings" % commit_hash)
            warnings = extract.etl_warnings(kdm_file, repo_dir, repo_id, commit_hash, class_file_mapping)
            logger.info("%s: %s warnings identified" % (commit_hash, len(warnings)))

            # Save warnings to db
            service_db.add_commit_warning_lines(warnings)

            # Get the line blames
            logger.info("%s: Obtaining history of warnings", commit_hash)
            line_blames = _get_line_blames(repo_dir, warnings)

            for blame in line_blames:
                blame["repo_id"] = repo_id
                blame['commit_id'] = commit_hash

            service_db.add_commit_warning_blames(line_blames)

        else:
            logger.error("%s: file %s does not exist. this is not normal as zip file existed" % (commit_hash, kdm_file))

    else:
        logger.info("%s: file %s does not exist. No file might have been analysed by static analysis tools" %
                    (commit_hash, zip_kdm_file))


def run_assimilator(repo_dir):
    adaptor_output_path = os.path.abspath(_get_adaptor_output_dir_path(repo_dir))
    assimilator_output_file_path = _get_kdm_file_output_path(repo_dir)
    assimilator_process = subprocess.Popen("%s --merge --kdmfile=%s --inputfile=%s" %
                                           (TOIF_EXECUTABLE, assimilator_output_file_path, adaptor_output_path),
                                           shell=True, cwd=os.path.abspath(repo_dir), stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE)

    # return the assimilator log results
    result = assimilator_process.communicate()[0]
    return result


def _extract_kdm_file(repo_dir):

    assimilator_output_file_path = _get_kdm_file_output_path(repo_dir)

    # TODO remove when toif is fixed and does not create two copies of the file: {name} and {name}.zip. File {name} is empty
    process = subprocess.Popen("rm %s; unzip %s" % (assimilator_output_file_path, assimilator_output_file_path + ".zip"),
                     shell=True, cwd=os.path.abspath(repo_dir), stdout=subprocess.PIPE,
                     stderr=subprocess.STDOUT)
    process.communicate()[0]


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

StaticGuruService()
