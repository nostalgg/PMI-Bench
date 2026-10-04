WITH item_totals AS (
    SELECT order_id, SUM(quantity * unit_price_cents) AS gross_cents
    FROM order_items GROUP BY order_id
), refund_totals AS (
    SELECT order_id, SUM(amount_cents) AS refunded_cents
    FROM refunds GROUP BY order_id
)
SELECT c.customer_id,
       c.name,
       COUNT(o.order_id) AS paid_order_count,
       COALESCE(SUM(i.gross_cents), 0) AS gross_cents,
       COALESCE(SUM(r.refunded_cents), 0) AS refunded_cents,
       COALESCE(SUM(i.gross_cents), 0) - COALESCE(SUM(r.refunded_cents), 0) AS net_cents
FROM customers AS c
LEFT JOIN orders AS o ON o.customer_id = c.customer_id AND o.status = 'paid'
LEFT JOIN item_totals AS i ON i.order_id = o.order_id
LEFT JOIN refund_totals AS r ON r.order_id = o.order_id
GROUP BY c.customer_id, c.name
ORDER BY c.customer_id;
