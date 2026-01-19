-- Initialize the inventory management database
-- This script sets up the basic database structure

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create schemas for better organization
CREATE SCHEMA IF NOT EXISTS inventory;
CREATE SCHEMA IF NOT EXISTS users;
CREATE SCHEMA IF NOT EXISTS locations;
CREATE SCHEMA IF NOT EXISTS audit;

-- Grant permissions
GRANT USAGE ON SCHEMA inventory TO inventory_user;
GRANT USAGE ON SCHEMA users TO inventory_user;
GRANT USAGE ON SCHEMA locations TO inventory_user;
GRANT USAGE ON SCHEMA audit TO inventory_user;

GRANT CREATE ON SCHEMA inventory TO inventory_user;
GRANT CREATE ON SCHEMA users TO inventory_user;
GRANT CREATE ON SCHEMA locations TO inventory_user;
GRANT CREATE ON SCHEMA audit TO inventory_user;