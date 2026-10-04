-- Intentionally buggy: joining two one-to-many relations multiplies amounts.
SELECT c.customer_id,
       c.name,
       COUNT(o.order_id) AS paid_order_count,
       SUM(i.quantity * i.unit_price_cents) AS gross_cents,
       SUM(r.amount_cents) AS refunded_cents,
       SUM(i.quantity * i.unit_price_cents) - SUM(r.amount_cents) AS net_cents
FROM customers AS c
JOIN orders AS o ON o.customer_id = c.customer_id
JOIN order_items AS i ON i.order_id = o.order_id
LEFT JOIN refunds AS r ON r.order_id = o.order_id
WHERE o.status = 'paid'
GROUP BY c.customer_id, c.name
ORDER BY c.customer_id;
