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
