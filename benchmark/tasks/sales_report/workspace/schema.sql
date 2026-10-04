CREATE TABLE customers (customer_id TEXT PRIMARY KEY, name TEXT NOT NULL);
CREATE TABLE orders (
    order_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers(customer_id),
    status TEXT NOT NULL CHECK (status IN ('paid', 'pending', 'cancelled'))
);
CREATE TABLE order_items (
    item_id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL REFERENCES orders(order_id),
    quantity INTEGER NOT NULL,
    unit_price_cents INTEGER NOT NULL
);
CREATE TABLE refunds (
    refund_id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL REFERENCES orders(order_id),
    amount_cents INTEGER NOT NULL
);
