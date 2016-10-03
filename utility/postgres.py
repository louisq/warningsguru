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