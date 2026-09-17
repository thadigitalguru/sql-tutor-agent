-- Hidden variant: extra customer with no orders, NULL country, and a customer
-- whose only orders are unpaid. Used to catch fragile join / NULL logic.
INSERT INTO customers (customer_id, name, country, signup_date) VALUES
  (1, 'Amina Ochieng', 'Kenya', '2024-01-15'),
  (2, 'John Smith', 'United States', '2024-02-01'),
  (3, 'Priya Patel', 'United Kingdom', '2024-02-20'),
  (4, 'Hans Mueller', 'Germany', '2024-03-05'),
  (5, 'Wanjiku Mwangi', 'Kenya', '2024-03-18'),
  (6, 'Marie Dubois', 'France', '2024-04-02'),
  (7, 'Brian Otieno', 'Kenya', '2024-04-21'),
  (8, 'Sofia Rossi', 'Italy', '2024-05-10'),
  (9, 'Noor Hassan', NULL, '2024-08-01'),
  (10, 'Kenji Sato', 'Japan', '2024-08-12');

INSERT INTO products (product_id, product_name, category, price) VALUES
  (1, 'Ceramic Mug', 'Home', 12.50),
  (2, 'Wireless Mouse', 'Electronics', 24.99),
  (3, 'Notebook Pack', 'Office', 8.00),
  (4, 'USB-C Cable', 'Electronics', 9.99),
  (5, 'Desk Lamp', 'Home', 39.00),
  (6, 'Mechanical Keyboard', 'Electronics', 89.00),
  (7, 'Water Bottle', 'Outdoors', 18.50),
  (8, 'Hoodie', 'Apparel', 45.00),
  (9, 'Standing Desk', 'Office', 320.00),
  (10, 'Monitor Arm', 'Office', 79.00),
  (11, 'Trail Backpack', 'Outdoors', 64.00),
  (12, 'Noise-Cancel Headset', 'Electronics', 129.00);

INSERT INTO orders (order_id, customer_id, order_date, status, total_amount, shipped_at) VALUES
  (101, 1, '2024-06-01', 'paid', 120.00, '2024-06-02'),
  (102, 1, '2024-06-18', 'paid', 80.00, '2024-06-19'),
  (103, 1, '2024-07-04', 'paid', 450.00, '2024-07-05'),
  (104, 2, '2024-06-03', 'paid', 200.00, '2024-06-04'),
  (105, 2, '2024-07-12', 'paid', 350.00, '2024-07-13'),
  (106, 3, '2024-06-08', 'paid', 40.00, '2024-06-09'),
  (107, 3, '2024-06-22', 'pending', 60.00, NULL),
  (108, 4, '2024-05-30', 'paid', 900.00, '2024-05-31'),
  (109, 5, '2024-06-11', 'paid', 25.00, '2024-06-12'),
  (110, 6, '2024-06-15', 'paid', 210.00, '2024-06-16'),
  (111, 6, '2024-07-01', 'paid', 300.00, '2024-07-02'),
  (112, 7, '2024-06-19', 'cancelled', 45.00, NULL),
  (113, 7, '2024-07-08', 'pending', 18.50, NULL),
  (114, 2, '2024-07-20', 'refunded', 24.99, '2024-07-21'),
  (115, 1, '2024-07-22', 'pending', 12.50, NULL),
  (116, 4, '2024-07-25', 'paid', 79.00, '2024-07-26'),
  (117, 5, '2024-07-28', 'cancelled', 8.00, NULL),
  (118, 6, '2024-08-01', 'paid', 64.00, '2024-08-02'),
  (119, 3, '2024-08-04', 'paid', 129.00, '2024-08-05'),
  (120, 7, '2024-08-09', 'paid', 39.00, '2024-08-10'),
  (121, 10, '2024-08-14', 'pending', 12.50, NULL);

INSERT INTO order_items (order_item_id, order_id, product_id, quantity, unit_price) VALUES
  (1, 101, 8, 1, 45.00),
  (2, 101, 5, 1, 39.00),
  (3, 101, 7, 2, 18.50),
  (4, 121, 1, 1, 12.50);
