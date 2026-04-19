CREATE TABLE public.inventory (
    id SERIAL PRIMARY KEY,
    vehicle_make VARCHAR(50),
    vehicle_model VARCHAR(50),
    vehicle_year INT,
    part_name VARCHAR(100),
    sample_vin VARCHAR(50),
    part_number VARCHAR(50),
    category VARCHAR(50),
    condition VARCHAR(50),
    quality_grade VARCHAR(20),
    rarity_level VARCHAR(20),
    min_price NUMERIC(10,2),
    max_price NUMERIC(10,2),
    stock INT,
    reserved_stock INT DEFAULT 0,
    lead_time_days INT
);

CREATE TABLE orders (

order_id TEXT PRIMARY KEY,

customer_name TEXT,
customer_email TEXT,

part_number TEXT,

price NUMERIC,

status TEXT,

created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

);

CREATE TABLE leads (
    id SERIAL PRIMARY KEY,
    full_name TEXT,
    phone TEXT,
    email TEXT,
    vehicle_make TEXT,
    year TEXT,
    vin TEXT,
    part_needed TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

DROP TABLE inventory;

SELECT * FROM leads ORDER BY id DESC;