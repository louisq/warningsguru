-- modify static_commit_processed to include_file_history

ALTER TABLE static_commit_processed ADD COLUMN file_history_processed TIMESTAMP DEFAULT null;

CREATE TABLE IF NOT EXISTS static_commit_file_history (
  REPO TEXT not null,
  COMMIT TEXT not null,
  FILE_PATH TEXT not null,
  PARENT_COMMIT TEXT,
  PARENT_FILE_PATH TEXT,
  FILE_ID TEXT not null,
  CREATED timestamp DEFAULT NOW(),
  CONSTRAINT static_commit_file_history_unique_key UNIQUE (repo, commit, file_path, parent_commit)
);

