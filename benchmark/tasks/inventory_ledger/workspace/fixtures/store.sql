CREATE TABLE stock(sku TEXT PRIMARY KEY,quantity INTEGER NOT NULL); CREATE TABLE movements(event_id TEXT PRIMARY KEY,sku TEXT NOT NULL,delta INTEGER NOT NULL);

-- Original synthetic starting records; not expected output.
INSERT INTO stock VALUES('001',10),('002',7);
