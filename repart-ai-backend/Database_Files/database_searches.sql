SELECT * FROM leads;

INSERT INTO leads (full_name, phone, email)
VALUES ('Test User', '1234567890', 'test@gmail.com');

SELECT current_database();

SELECT * FROM inventory;

SELECT * FROM leads;

SELECT * FROM orders;

SELECT column_name FROM information_schema.columns WHERE table_name = 'leads';

SELECT column_name FROM information_schema.columns WHERE table_name = 'orders';

SELECT column_name FROM information_schema.columns WHERE table_name = 'inventory';

SELECT * FROM inventory where part_number = 'TAI-KI2018-7';