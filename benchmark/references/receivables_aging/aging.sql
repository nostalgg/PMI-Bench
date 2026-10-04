WITH payments_to_date AS (
 SELECT p.invoice_id, SUM(p.amount_cents) AS paid_cents
 FROM payments p, report_config cfg
 WHERE p.status='posted' AND p.paid_on <= cfg.as_of
 GROUP BY p.invoice_id
), open_invoices AS (
 SELECT i.customer_id, MAX(i.amount_cents-COALESCE(p.paid_cents,0),0) AS balance,
        CAST(julianday(cfg.as_of)-julianday(i.due_on) AS INTEGER) AS days_late
 FROM invoices i CROSS JOIN report_config cfg
 LEFT JOIN payments_to_date p ON p.invoice_id=i.invoice_id
 WHERE i.status='issued' AND i.issued_on <= cfg.as_of
)
SELECT c.customer_id,
 COALESCE(SUM(CASE WHEN o.days_late<=0 THEN o.balance ELSE 0 END),0) AS not_due_cents,
 COALESCE(SUM(CASE WHEN o.days_late BETWEEN 1 AND 30 THEN o.balance ELSE 0 END),0) AS days_1_30_cents,
 COALESCE(SUM(CASE WHEN o.days_late BETWEEN 31 AND 60 THEN o.balance ELSE 0 END),0) AS days_31_60_cents,
 COALESCE(SUM(CASE WHEN o.days_late>=61 THEN o.balance ELSE 0 END),0) AS days_61_plus_cents
FROM customers c LEFT JOIN open_invoices o ON o.customer_id=c.customer_id
GROUP BY c.customer_id ORDER BY c.customer_id;
