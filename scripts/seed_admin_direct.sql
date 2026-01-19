-- Direct SQL script to create admin user and sample data
-- This can be run directly against the PostgreSQL database

-- Create admin role if it doesn't exist
INSERT INTO roles (id, name, description, permissions, created_at, updated_at)
VALUES (
    gen_random_uuid(),
    'admin',
    'System Administrator with full access',
    '["*"]',
    NOW(),
    NOW()
) ON CONFLICT (name) DO NOTHING;

-- Create admin user (password is 'secret')
-- The password hash is bcrypt for 'secret'
INSERT INTO users (id, username, email, password_hash, active, role_id, created_at, updated_at)
VALUES (
    gen_random_uuid(),
    'admin',
    'admin@inventory.local',
    '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW',
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

-- Create location types
INSERT INTO location_types (id, name, description, created_at, updated_at)
VALUES 
    (gen_random_uuid(), 'Warehouse', 'Storage and distribution facility', NOW(), NOW()),
    (gen_random_uuid(), 'Office', 'Administrative office space', NOW(), NOW()),
    (gen_random_uuid(), 'Storage Room', 'Small storage area', NOW(), NOW())
ON CONFLICT (name) DO NOTHING;

-- Create sample locations
INSERT INTO locations (id, name, description, location_metadata, location_type_id, created_at, updated_at)
VALUES 
    (gen_random_uuid(), 'Main Warehouse', 'Primary storage facility', '{}', 
     (SELECT id FROM location_types WHERE name = 'Warehouse'), NOW(), NOW()),
    (gen_random_uuid(), 'Corporate Office', 'Main administrative office', '{}', 
     (SELECT id FROM location_types WHERE name = 'Office'), NOW(), NOW()),
    (gen_random_uuid(), 'IT Storage', 'IT equipment storage room', '{}', 
     (SELECT id FROM location_types WHERE name = 'Storage Room'), NOW(), NOW())
ON CONFLICT DO NOTHING;

-- Create item types
INSERT INTO item_types (id, name, description, category, created_at, updated_at)
VALUES 
    (gen_random_uuid(), 'Equipment', 'Physical equipment and machinery', 'PARENT', NOW(), NOW()),
    (gen_random_uuid(), 'Furniture', 'Office and warehouse furniture', 'PARENT', NOW(), NOW()),
    (gen_random_uuid(), 'Component', 'Individual components and parts', 'CHILD', NOW(), NOW()),
    (gen_random_uuid(), 'Accessory', 'Equipment accessories', 'CHILD', NOW(), NOW())
ON CONFLICT DO NOTHING;

-- Display success message
SELECT 'Admin user and sample data created successfully!' as message,
       'Username: admin' as username,
       'Password: secret' as password,
       'Role: admin' as role;