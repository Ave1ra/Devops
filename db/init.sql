DO $$ BEGIN
  IF NOT EXISTS (SELECT FROM pg_database WHERE datname = 'test') THEN
    CREATE DATABASE test;
  END IF;
END $$;
GRANT ALL PRIVILEGES ON DATABASE test to postgres;
CREATE USER repl_user WITH REPLICATION ENCRYPTED PASSWORD '1234';
SELECT pg_create_physical_replication_slot('replication_slot');
CREATE TABLE IF NOT EXISTS emails (id SERIAL PRIMARY KEY, email VARCHAR(255));
CREATE TABLE IF NOT EXISTS phone_numbers (id SERIAL PRIMARY KEY, phone_number VARCHAR(50));
INSERT INTO emails (email) VALUES ('example1@example.com'), ('example2@example.com');
INSERT INTO phone_numbers (phone_number) VALUES ('1234567890'), ('0987654321');
