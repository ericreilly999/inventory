-- Manual migration script to rename name to sku
-- Run this directly against the database if automated migration fails

-- Check current state
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name IN ('parent_items', 'child_items') 
AND column_name IN ('name', 'sku')
ORDER BY table_name, column_name;

-- Rename columns
ALTER TABLE parent_items RENAME COLUMN name TO sku;
ALTER TABLE child_items RENAME COLUMN name TO sku;

-- Update alembic version table
UPDATE alembic_version SET version_num = '49871d03964c';

-- Verify changes
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name IN ('parent_items', 'child_items') 
AND column_name IN ('name', 'sku')
ORDER BY table_name, column_name;

SELECT * FROM alembic_version;
