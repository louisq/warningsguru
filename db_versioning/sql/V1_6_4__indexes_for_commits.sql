CREATE INDEX commit_commit_hash_idx ON commits (commit_hash);

CREATE INDEX commit_author_date_unix_timestamp_idx ON commits (author_date_unix_timestamp);

CREATE INDEX static_commit_processed_commit_idx on STATIC_COMMIT_PROCESSED (commit);
