-- Platform warehouse used by mid-senior SQL: star schema, SCD2, org hierarchy,
-- event streams, and model/inference logs. Small enough to inspect by hand.
PRAGMA foreign_keys = ON;

CREATE TABLE employees (
    employee_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    title TEXT NOT NULL,
    manager_id INTEGER,
    department TEXT NOT NULL,
    hired_at TEXT NOT NULL,
    FOREIGN KEY (manager_id) REFERENCES employees (employee_id)
);

CREATE TABLE accounts (
    account_id INTEGER PRIMARY KEY,
    account_name TEXT NOT NULL,
    plan TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE users (
    user_id INTEGER PRIMARY KEY,
    email TEXT NOT NULL,
    country TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE account_members (
    account_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    member_role TEXT NOT NULL,
    effective_from TEXT NOT NULL,
    effective_to TEXT,
    PRIMARY KEY (account_id, user_id, effective_from),
    FOREIGN KEY (account_id) REFERENCES accounts (account_id),
    FOREIGN KEY (user_id) REFERENCES users (user_id)
);

CREATE TABLE dim_customer (
    customer_sk INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    country TEXT,
    plan TEXT NOT NULL,
    valid_from TEXT NOT NULL,
    valid_to TEXT NOT NULL,
    is_current INTEGER NOT NULL
);

CREATE TABLE dim_product (
    product_sk INTEGER PRIMARY KEY,
    product_id INTEGER NOT NULL,
    category TEXT NOT NULL,
    product_name TEXT NOT NULL
);

CREATE TABLE fact_orders (
    order_line_id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL,
    customer_id INTEGER NOT NULL,
    product_sk INTEGER NOT NULL,
    order_ts TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    amount REAL NOT NULL,
    status TEXT NOT NULL,
    FOREIGN KEY (product_sk) REFERENCES dim_product (product_sk)
);

CREATE TABLE events (
    event_id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    event_name TEXT NOT NULL,
    event_ts TEXT NOT NULL,
    properties_json TEXT,
    FOREIGN KEY (user_id) REFERENCES users (user_id)
);

CREATE TABLE model_runs (
    run_id INTEGER PRIMARY KEY,
    model_name TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    started_at TEXT NOT NULL,
    tokens_in INTEGER NOT NULL,
    tokens_out INTEGER NOT NULL,
    cost_usd REAL NOT NULL,
    status TEXT NOT NULL
);

CREATE TABLE predictions (
    prediction_id INTEGER PRIMARY KEY,
    entity_id INTEGER NOT NULL,
    model_name TEXT NOT NULL,
    predicted_label TEXT NOT NULL,
    score REAL NOT NULL,
    predicted_at TEXT NOT NULL
);

CREATE TABLE labels (
    entity_id INTEGER PRIMARY KEY,
    true_label TEXT NOT NULL,
    labeled_at TEXT NOT NULL
);

CREATE TABLE user_features (
    user_id INTEGER NOT NULL,
    feature_date TEXT NOT NULL,
    orders_7d INTEGER NOT NULL,
    spend_7d REAL NOT NULL,
    computed_at TEXT NOT NULL,
    PRIMARY KEY (user_id, feature_date)
);

CREATE TABLE documents (
    doc_id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    source TEXT NOT NULL,
    metadata_json TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE chunks (
    chunk_id INTEGER PRIMARY KEY,
    doc_id INTEGER NOT NULL,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    token_count INTEGER NOT NULL,
    FOREIGN KEY (doc_id) REFERENCES documents (doc_id)
);
