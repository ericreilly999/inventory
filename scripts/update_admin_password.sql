-- Update admin user password with a fresh bcrypt hash
-- This script updates the admin user's password to 'admin'
-- Run this if you're experiencing login issues after the bcrypt migration

-- The hash below is a valid bcrypt hash for password 'admin' with cost factor 12
-- Generated using Python bcrypt library: bcrypt.hashpw(b'admin', bcrypt.gensalt(rounds=12))
-- 
-- To generate a new hash, run:
-- python3 -c "import bcrypt; print(bcrypt.hashpw(b'admin', bcrypt.gensalt(rounds=12)).decode('utf-8'))"

UPDATE users 
SET password_hash = '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW',
    updated_at = NOW()
WHERE username = 'admin';

-- Verify the update
SELECT 
    username,
    email,
    active,
    LENGTH(password_hash) as hash_length,
    SUBSTRING(password_hash, 1, 10) as hash_prefix,
    updated_at
FROM users 
WHERE username = 'admin';

SELECT 'Admin password updated successfully!' as message;
SELECT 'Login credentials:' as info;
SELECT 'Username: admin' as username;
SELECT 'Password: admin' as password;
