CREATE TABLE products(sku TEXT PRIMARY KEY,description TEXT NOT NULL,cost_cents INTEGER NOT NULL,retail_price_cents INTEGER,active INTEGER NOT NULL);

-- Original synthetic starting records; not expected output.
INSERT INTO products VALUES('001','Existing part',100,999,1); INSERT INTO products VALUES('keep','Manual-only',200,500,1);
