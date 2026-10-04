CREATE TABLE customer_history(customer_id TEXT NOT NULL,name TEXT NOT NULL,valid_from TEXT NOT NULL,valid_to TEXT,PRIMARY KEY(customer_id,valid_from)); CREATE UNIQUE INDEX one_current ON customer_history(customer_id) WHERE valid_to IS NULL;

-- Original synthetic starting records; not expected output.
INSERT INTO customer_history VALUES('001','Original workshop','2024-01-01',NULL);
