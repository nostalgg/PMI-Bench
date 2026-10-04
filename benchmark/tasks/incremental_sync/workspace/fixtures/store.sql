CREATE TABLE replica(record_id TEXT PRIMARY KEY,value TEXT NOT NULL); CREATE TABLE checkpoint(singleton INTEGER PRIMARY KEY CHECK(singleton=1),sequence INTEGER NOT NULL); INSERT INTO checkpoint VALUES(1,0);

-- Original synthetic starting records; not expected output.
INSERT INTO replica VALUES('001','old');
