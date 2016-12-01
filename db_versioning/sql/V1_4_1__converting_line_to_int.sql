ALTER TABLE static_commit_line_warning ALTER COLUMN line TYPE integer USING (trim(line)::integer);

