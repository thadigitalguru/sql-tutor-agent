INSERT INTO employees (employee_id, name, title, manager_id, department, hired_at) VALUES
  (1, 'Maya Chen', 'CTO', NULL, 'Engineering', '2020-01-06'),
  (2, 'Luis Alvarez', 'Engineering Manager', 1, 'Engineering', '2021-03-15'),
  (3, 'Aisha Khan', 'Staff Engineer', 2, 'Engineering', '2022-01-10'),
  (4, 'Tom Reed', 'Engineer', 2, 'Engineering', '2023-04-01'),
  (5, 'Priya Shah', 'Data Manager', 1, 'Data', '2021-07-12'),
  (6, 'Ken Okonkwo', 'Analytics Engineer', 5, 'Data', '2022-09-01'),
  (7, 'Elena Rossi', 'ML Engineer', 5, 'Data', '2023-02-14'),
  (8, 'Jonah Pike', 'Support Lead', 1, 'Support', '2021-11-02'),
  (9, 'Lin Park', 'Support Specialist', 8, 'Support', '2024-01-08');

INSERT INTO accounts (account_id, account_name, plan, created_at) VALUES
  (1, 'Acme', 'enterprise', '2023-01-01'),
  (2, 'Globex', 'team', '2023-06-01'),
  (3, 'Initech', 'free', '2024-01-01'),
  (4, 'Umbrella', 'enterprise', '2024-02-01');

INSERT INTO users (user_id, email, country, created_at) VALUES
  (1, 'ada@acme.test', 'Kenya', '2023-01-10'),
  (2, 'ben@acme.test', 'United States', '2023-02-01'),
  (3, 'cam@globex.test', 'United Kingdom', '2023-06-15'),
  (4, 'dee@globex.test', 'Germany', '2023-07-01'),
  (5, 'eve@initech.test', 'France', '2024-01-20'),
  (6, 'fay@initech.test', 'Kenya', '2024-02-01'),
  (7, 'gus@none.test', 'United States', '2024-03-01'),
  (8, 'hao@acme.test', 'Kenya', '2023-01-12');

INSERT INTO account_members (account_id, user_id, member_role, effective_from, effective_to) VALUES
  (1, 1, 'owner', '2023-01-10', NULL),
  (1, 2, 'member', '2023-02-01', NULL),
  (1, 8, 'admin', '2023-01-12', '2024-01-01'),
  (2, 3, 'owner', '2023-06-15', NULL),
  (2, 4, 'member', '2023-07-01', NULL),
  (3, 5, 'owner', '2024-01-20', NULL),
  (3, 6, 'member', '2024-02-01', '2024-04-01');

INSERT INTO dim_customer (customer_sk, customer_id, country, plan, valid_from, valid_to, is_current) VALUES
  (101, 1, 'Kenya', 'free', '2023-01-01', '2024-03-01', 0),
  (102, 1, 'United States', 'team', '2024-03-01', '9999-12-31', 1),
  (201, 2, 'United States', 'free', '2023-01-01', '9999-12-31', 1),
  (301, 3, 'United Kingdom', 'team', '2023-06-01', '2024-01-15', 0),
  (302, 3, 'United Kingdom', 'enterprise', '2024-01-15', '9999-12-31', 1);

INSERT INTO dim_product (product_sk, product_id, category, product_name) VALUES
  (1, 10, 'Home', 'Ceramic Mug'),
  (2, 20, 'Electronics', 'Wireless Mouse'),
  (3, 30, 'Office', 'Standing Desk');

INSERT INTO fact_orders (order_line_id, order_id, customer_id, product_sk, order_ts, quantity, amount, status) VALUES
  (1, 10, 1, 1, '2024-02-10', 1, 40.00, 'paid'),
  (2, 10, 1, 2, '2024-02-10', 1, 60.00, 'paid'),
  (3, 11, 1, 3, '2024-04-01', 1, 320.00, 'paid'),
  (4, 12, 2, 1, '2024-03-01', 2, 80.00, 'paid'),
  (5, 13, 3, 3, '2024-01-10', 1, 200.00, 'paid'),
  (6, 14, 3, 1, '2024-02-01', 3, 120.00, 'paid');

INSERT INTO events (event_id, user_id, event_name, event_ts, properties_json) VALUES
  (8, 3, 'page_view', '2024-06-01 09:00:00', '{"page":"/pricing","ref":"ad"}'),
  (1, 1, 'page_view', '2024-06-01 10:00:00', '{"page":"/home","ref":"direct"}'),
  (2, 1, 'click', '2024-06-01 10:05:00', '{"page":"/pricing","ref":"direct"}'),
  (3, 1, 'purchase', '2024-06-01 10:08:00', '{"page":"/checkout","amount":40}'),
  (6, 2, 'page_view', '2024-06-01 11:00:00', '{"page":"/home","ref":"email"}'),
  (7, 2, 'click', '2024-06-01 11:40:00', '{"page":"/blog","ref":"email"}'),
  (4, 1, 'page_view', '2024-06-01 12:00:00', '{"page":"/home","ref":"direct"}'),
  (5, 1, 'click', '2024-06-01 12:04:00', '{"page":"/docs","ref":"direct"}');

INSERT INTO model_runs (run_id, model_name, user_id, started_at, tokens_in, tokens_out, cost_usd, status) VALUES
  (1, 'gpt-4o-mini', 1, '2024-06-02 08:00:00', 1200, 400, 0.020, 'success'),
  (2, 'gpt-4o', 1, '2024-06-02 08:10:00', 800, 350, 0.150, 'success'),
  (3, 'gpt-4o-mini', 2, '2024-06-02 09:00:00', 900, 200, 0.012, 'success'),
  (4, 'embed-small', 3, '2024-06-02 09:30:00', 4000, 0, 0.004, 'success'),
  (5, 'gpt-4o', 2, '2024-06-02 10:00:00', 500, 0, 0.000, 'failed'),
  (6, 'gpt-4o-mini', 7, '2024-06-03 11:00:00', 300, 80, 0.006, 'success');

INSERT INTO predictions (prediction_id, entity_id, model_name, predicted_label, score, predicted_at) VALUES
  (1, 1, 'churn-v1', 'churn', 0.40, '2024-05-01 00:00:00'),
  (2, 1, 'churn-v1', 'churn', 0.81, '2024-06-01 00:00:00'),
  (3, 2, 'churn-v1', 'stay', 0.62, '2024-06-01 00:00:00'),
  (4, 2, 'churn-v1', 'churn', 0.55, '2024-06-15 00:00:00'),
  (5, 3, 'churn-v1', 'stay', 0.91, '2024-04-01 00:00:00'),
  (6, 4, 'churn-v1', 'churn', 0.22, '2024-06-01 00:00:00'),
  (7, 4, 'churn-v1', 'stay', 0.70, '2024-06-02 00:00:00');

INSERT INTO labels (entity_id, true_label, labeled_at) VALUES
  (3, 'stay', '2024-05-01'),
  (4, 'churn', '2024-06-03'),
  (1, 'churn', '2024-06-05'),
  (2, 'stay', '2024-06-20');

INSERT INTO user_features (user_id, feature_date, orders_7d, spend_7d, computed_at) VALUES
  (1, '2024-05-31', 2, 100.00, '2024-06-01 01:00:00'),
  (1, '2024-06-07', 5, 400.00, '2024-06-08 01:00:00'),
  (2, '2024-06-01', 1, 80.00, '2024-06-02 01:00:00'),
  (2, '2024-06-18', 4, 250.00, '2024-06-19 01:00:00'),
  (3, '2024-04-20', 0, 0.00, '2024-04-21 01:00:00'),
  (4, '2024-05-30', 3, 90.00, '2024-05-31 01:00:00');

INSERT INTO documents (doc_id, title, source, metadata_json, updated_at) VALUES
  (1, 'Oncall runbook', 'wiki', '{"team":"eng","pii":0}', '2024-06-01'),
  (2, 'Customer contract', 'gdrive', '{"team":"legal","pii":1}', '2024-05-01'),
  (3, 'Churn model card', 'wiki', '{"team":"ml","pii":0}', '2024-07-01');

INSERT INTO chunks (chunk_id, doc_id, chunk_index, chunk_text, token_count) VALUES
  (11, 1, 0, 'Page the primary oncall if error rate exceeds 2 percent.', 18),
  (12, 1, 1, 'Escalate to the CTO after 30 minutes without ack.', 14),
  (21, 2, 0, 'The customer name and billing address are stored in Salesforce.', 16),
  (22, 2, 1, 'Renewal terms auto-extend unless cancelled in writing.', 12),
  (31, 3, 0, 'churn-v1 is a gradient boosting model trained on 90 days of orders.', 20);
