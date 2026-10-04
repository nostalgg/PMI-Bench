-- Original synthetic starting records; not expected output.
INSERT INTO customers VALUES('001'),('002'); INSERT INTO report_config VALUES('2024-03-31'); INSERT INTO invoices VALUES('INV-001','001',10000,'2024-01-01','2024-03-01','issued'); INSERT INTO payments VALUES('P1','INV-001',3000,'2024-03-15','posted'),('P2','INV-001',7000,'2024-04-02','posted');
