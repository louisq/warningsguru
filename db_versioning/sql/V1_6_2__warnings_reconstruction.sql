
ALTER TABLE static_commit_processed ADD COLUMN warnings_analysis_processing TIMESTAMP DEFAULT null;
ALTER TABLE static_commit_processed ADD COLUMN warnings_analysis_processed TIMESTAMP DEFAULT null;

CREATE TABLE IF NOT EXISTS static_commit_warnings_processed (
  REPO TEXT not null,
  COMMIT TEXT not null,
  FILE_PATH TEXT not null,
  LINE TEXT not null,
  ORIGIN_COMMIT TEXT not null,
  ORIGIN_FILE_PATH TEXT not null,
  ORIGIN_LINE TEXT not null,
  WEAKNESS TEXT not null,
  SFP TEXT not null,
  CWE TEXT not null,
  GENERATOR_TOOL TEXT not null,
  FILE_ID TEXT not null,
  NEW_WARNING BOOLEAN not null,
  RECOVERED_WARNING BOOLEAN not null,
  CREATED timestamp DEFAULT NOW(),
PRIMARY KEY (REPO, COMMIT, FILE_PATH, LINE, WEAKNESS));
