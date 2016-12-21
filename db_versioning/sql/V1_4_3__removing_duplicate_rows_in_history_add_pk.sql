

CREATE TABLE COMMIT_HISTORY_GRAPH_TEMP AS
  (SELECT distinct on (repo, commit, parent_commit)
     repo, commit, parent_commit, created
  FROM COMMIT_HISTORY_GRAPH as chg);
  --GROUP BY (chg.repo, chg.commit, chg.parent_commit));

DROP TABLE COMMIT_HISTORY_GRAPH;

ALTER TABLE COMMIT_HISTORY_GRAPH_TEMP
  RENAME TO COMMIT_HISTORY_GRAPH;

ALTER TABLE COMMIT_HISTORY_GRAPH ADD PRIMARY KEY (repo, commit, parent_commit);
