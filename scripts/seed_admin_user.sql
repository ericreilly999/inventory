-- Seed script to create admin user and basic data
-- This script should be run after the initial migration

-- Create admin role
INSERT INTO roles (id, name, description, permissions, created_at, updated_at)
VALUES (
    gen_random_uuid(),
    'admin',
    'System Administrator with full access',
    '["*"]',
    NOW(),
    NOW()
) ON CONFLICT (name) DO NOTHING;

-- Create admin user with password 'admin'
-- Password hash generated with bcrypt for 'admin' (cost factor 12)
-- Hash generated using: python -c "from passlib.context import CryptContext; print(CryptContext(schemes=['bcrypt']).hash('admin'))"
INSERT INTO users (id, username, email, password_hash, active, role_id, created_at, updated_at)
VALUES (
    gen_random_uuid(),
    'admin',
    'admin@inventory.local',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU2xN7qhV/7e', -- bcrypt hash for 'admin'
    true,
    (SELECT id FROM roles WHERE name = 'admin'),
    NOW(),
    NOW()
) ON CONFLICT (username) DO UPDATE SET
    email = EXCLUDED.email,
    password_hash = EXCLUDED.password_hash,
    active = EXCLUDED.active,
    role_id = EXCLUDED.role_id,
    updated_at = EXCLUDED.updated_at;

-- Create basic location types
INSERT INTO location_types (id, name, description, created_at, updated_at)
VALUES 
    (gen_random_uuid(), 'Warehouse', 'Storage and distribution facility', NOW(), NOW()),
    (gen_random_uuid(), 'Office', 'Administrative office space', NOW(), NOW()),
    (gen_random_uuid(), 'Storage Room', 'Small storage area', NOW(), NOW())
ON CONFLICT (name) DO NOTHING;

-- Create sample locations
INSERT INTO locations (id, name, description, location_metadata, location_type_id, created_at, updated_at)
VALUES 
    (
        gen_random_uuid(),
        'Main Warehouse',
        'Primary storage facility',
        '{}',
        (SELECT id FROM location_types WHERE name = 'Warehouse' LIMIT 1),
        NOW(),
        NOW()
    ),
    (
        gen_random_uuid(),
        'Corporate Office',
        'Main administrative office',
        '{}',
        (SELECT id FROM location_types WHERE name = 'Office' LIMIT 1),
        NOW(),
        NOW()
    ),
    (
        gen_random_uuid(),
        'IT Storage',
        'IT equipment storage room',
        '{}',
        (SELECT id FROM location_types WHERE name = 'Storage Room' LIMIT 1),
        NOW(),
        NOW()
    );

-- Create sample item types
INSERT INTO item_types (id, name, description, category, created_at, updated_at)
VALUES 
    (gen_random_uuid(), 'Equipment', 'Physical equipment and machinery', 'PARENT', NOW(), NOW()),
    (gen_random_uuid(), 'Furniture', 'Office and warehouse furniture', 'PARENT', NOW(), NOW()),
    (gen_random_uuid(), 'Component', 'Individual components and parts', 'CHILD', NOW(), NOW()),
    (gen_random_uuid(), 'Accessory', 'Equipment accessories', 'CHILD', NOW(), NOW());

-- Display success message
SELECT 'Admin user and sample data created successfully!' as message;
SELECT 'Login credentials:' as info;
SELECT 'Username: admin' as username;
SELECT 'Password: admin' as password;