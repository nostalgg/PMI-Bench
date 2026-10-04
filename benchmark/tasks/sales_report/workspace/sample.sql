INSERT INTO customers VALUES ('C01', 'Aurora'), ('C02', 'Aurora'), ('C03', 'Boreale');
INSERT INTO orders VALUES ('O01', 'C01', 'paid'), ('O02', 'C02', 'pending');
INSERT INTO order_items VALUES ('I01', 'O01', 2, 500), ('I02', 'O01', 1, 1000);
INSERT INTO refunds VALUES ('R01', 'O01', 100), ('R02', 'O01', 200);
