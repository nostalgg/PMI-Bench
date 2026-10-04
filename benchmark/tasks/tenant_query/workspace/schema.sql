CREATE TABLE orders(tenant_id TEXT NOT NULL,order_id TEXT NOT NULL,amount_cents INTEGER NOT NULL,created_at TEXT NOT NULL,PRIMARY KEY(tenant_id,order_id));
