CREATE TABLE orders(tenant_id TEXT NOT NULL,order_id TEXT NOT NULL,amount_cents INTEGER NOT NULL,created_at TEXT NOT NULL,PRIMARY KEY(tenant_id,order_id));

-- Original synthetic starting records; not expected output.
INSERT INTO orders VALUES('A','001',300,'2024-01-01'),('B','001',999,'2024-01-01');
