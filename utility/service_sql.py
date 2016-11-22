import config
from postgres import Postgres

class Service_DB:

    def __init__(self, reprocess_failures_hours):
        self.db = Postgres(config.get_local_settings())
        self.REPROCESS_FAILURES_HOURS = reprocess_failures_hours

    def get_unprocessed_commits(self):
        cursor = self.db.get_cursor()

        if config.REPO_TO_ANALYSE:
            query = """
                    SELECT repository_id, commit_hash
                    FROM COMMITS
                    WHERE COMMITS.COMMIT_HASH NOT IN (SELECT COMMIT FROM STATIC_COMMIT_PROCESSED AS PROCESSED)
                    AND repository_id = '%s'
                    ORDER BY author_date_unix_timestamp
                    LIMIT 10;
                    """ % config.REPO_TO_ANALYSE
        else:
            query = """
                    SELECT repository_id, commit_hash
                    FROM COMMITS
                    WHERE COMMITS.COMMIT_HASH NOT IN (SELECT COMMIT FROM STATIC_COMMIT_PROCESSED AS PROCESSED)
                    ORDER BY author_date_unix_timestamp
                    LIMIT 10;
                    """

        cursor.execute(query)
        rows = cursor.fetchall()

        REPO = 0
        COMMIT = 1

        commits = []

        for row in rows:
            commits.append({"repo": row[REPO], "commit": row[COMMIT]})

        return commits

    """
    Delete any records of previous runs that have failed over an hour ago
    """
    def truncate_commit_processing(self):
        cursor = self.db.get_cursor()
        cursor.execute(
            """
            DELETE FROM STATIC_COMMIT_PROCESSED
            WHERE STATUS <> 'PROCESSED' AND modified < NOW() - INTERVAL '360 minute';
            --WHERE modified < NOW() - INTERVAL '%s HOUR';
            """ % self.REPROCESS_FAILURES_HOURS
        )
        self.db.db.commit()

    def queued_commit(self, commits):
        cursor = self.db.get_cursor()

        cursor.executemany("""
            INSERT INTO STATIC_COMMIT_PROCESSED
            (REPO, COMMIT, STATUS)
            VALUES
            (%(repo)s, %(commit)s, 'QUEUED');
            """, commits)
        self.db.db.commit()

    def processing_commit(self, repo, commit):
        cursor = self.db.get_cursor()

        cursor.execute("""
            UPDATE STATIC_COMMIT_PROCESSED
             SET STATUS = 'PROCESSING', MODIFIED = NOW()
             WHERE REPO = %s AND COMMIT = %s;
            """, (repo, commit))
        self.db.db.commit()

    def processed_commit(self, repo, commit, build, log=""):
        cursor = self.db.get_cursor()

        cursor.execute("""
            UPDATE STATIC_COMMIT_PROCESSED
             SET STATUS = 'PROCESSED', BUILD = %s, BUILD_LOG = %s, MODIFIED = NOW()
             WHERE REPO = %s AND COMMIT = %s;
            """, (build, log, repo, commit))
        self.db.db.commit()

    def add_commit_warning_lines(self, warnings):

        cursor = self.db.get_cursor()
        cursor.executemany("""
        INSERT INTO STATIC_COMMIT_LINE_WARNING
        (REPO, COMMIT, RESOURCE, LINE, SFP, CWE, GENERATOR_TOOL, WEAKNESS)
        VALUES
        (%(repo_id)s, %(commit_id)s, %(resource)s, %(line_number)s, %(SFP)s, %(CWE)s, %(generator_tool)s, %(description)s)
        """, warnings)

    def add_commit_warning_blames(self, blames):

        cursor = self.db.get_cursor()
        cursor.executemany("""
        INSERT INTO static_commit_line_blame
        (REPO, COMMIT, RESOURCE, LINE, ORIGIN_COMMIT, ORIGIN_RESOURCE, ORIGIN_LINE, IS_NEW_LINE)
        VALUES
        (%(repo_id)s, %(commit_id)s, %(resource)s, %(line)s, %(origin_commit)s, %(origin_resource)s, %(origin_line)s, %(is_new_line)s)
        """, blames)

    def add_commit_history_graph(self, relations):
        cursor = self.db.get_cursor()
        cursor.executemany("""
        INSERT INTO commit_history_graph
        (REPO, COMMIT, PARENT_COMMIT)
        VALUES
        (%(repo_id)s, %(commit_id)s, %(parent_commit)s)
        """, relations)
