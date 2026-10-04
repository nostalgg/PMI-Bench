CREATE TABLE enrichment(record_id TEXT PRIMARY KEY,input_sha256 TEXT NOT NULL,label TEXT NOT NULL,model TEXT NOT NULL);

-- Original synthetic starting records; not expected output.
-- Fresh cache; no existing enrichment rows.
