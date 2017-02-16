CREATE INDEX static_commit_line_warning_weakness_idx ON static_commit_line_warning (weakness);

CREATE INDEX static_commit_line_blame_origin_idx ON static_commit_line_blame (origin_commit, origin_resource, origin_line);

CREATE INDEX static_commit_file_history_commit_idx ON static_commit_file_history (repo, commit);

CREATE INDEX static_commit_file_history_file_id_idx ON static_commit_file_history (file_id);

CREATE INDEX static_commit_file_history_id_commit_file_idx ON static_commit_file_history(file_id, repo, commit, file_path);

ALTER TABLE static_commit_file_history ADD COLUMN alt_commit text;

UPDATE static_commit_file_history
SET alt_commit = concat('^', substring(commit from 1 for 39));

CREATE INDEX static_commit_file_history_id_commit_alt_file_idx ON static_commit_file_history(file_id, repo, alt_commit, file_path);
