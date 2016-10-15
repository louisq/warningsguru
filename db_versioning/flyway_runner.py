"""

"""
import os
import subprocess

from utility.Logging import logger


def migrate_db(host, port, database, username, password):

    # TODO check if the tool is running on a windows machine

    postgresql_path = "jdbc:postgresql://%s:%s/%s" % (host, port, database)

    logger.info("Running flyway migrate on %s" % postgresql_path)

    process = subprocess.Popen("./flyway migrate -url=%s -user=%s -password=%s" %
                               (postgresql_path, username, password),
                               shell=True,
                               cwd=os.path.dirname(os.path.realpath(__file__)),
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)

    result = process.communicate()[0]
    return_code = process.returncode

    if return_code != 0:
        logger.warn(result)
        raise RuntimeError("Application failed to update or validate the state of it's database. Check the logs to "
                           "fix the current issue.")
    logger.info(result)
    logger.info("Connection to database confirmed and state of database is valid for application to run")
