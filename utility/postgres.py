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

import logging
import psycopg2


class Postgres:

    DATABASE_HOST = ""
    DATABASE_NAME = ""
    DATABASE_USERNAME = ""
    DATABASE_PASSWORD = ""

    def __init__(self, db_config):
        self.logger = logging.getLogger("Postgres")

        # db_config = settings.get_local_settings()
        if db_config:
            self.DATABASE_HOST = db_config['DATABASE_HOST']
            self.DATABASE_NAME = db_config['DATABASE_NAME']
            self.DATABASE_USERNAME = db_config['DATABASE_USERNAME']
            self.DATABASE_PASSWORD = db_config['DATABASE_PASSWORD']
        else:
            print "db_config not configured"

        try:
            if self.DATABASE_PASSWORD:
                db = psycopg2.connect("dbname='%s' user='%s' host='%s' password='%s'" %
                                      (self.DATABASE_NAME, self.DATABASE_USERNAME, self.DATABASE_HOST, self.DATABASE_PASSWORD))
            else:
                db = psycopg2.connect("dbname='%s' host='%s' user='%s'" %
                                      (self.DATABASE_NAME, self.DATABASE_HOST, self.DATABASE_USERNAME))

            self.db = db

        except Exception as e:
            print "Failed to connect to database: %s" % e.message

    def get_cursor(self):
        return self.db.cursor()