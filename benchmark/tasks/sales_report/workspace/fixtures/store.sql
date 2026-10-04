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

INSERT INTO customers VALUES ('C01', 'Aurora'), ('C02', 'Aurora'), ('C03', 'Boreale');
INSERT INTO orders VALUES ('O01', 'C01', 'paid'), ('O02', 'C02', 'pending');
INSERT INTO order_items VALUES ('I01', 'O01', 2, 500), ('I02', 'O01', 1, 1000);
INSERT INTO refunds VALUES ('R01', 'O01', 100), ('R02', 'O01', 200);
