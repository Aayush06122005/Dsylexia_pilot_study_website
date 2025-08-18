-- Test script to verify reading tasks setup
USE dyslexia_study;

-- Check if reading_tasks table exists
SHOW TABLES LIKE 'reading_tasks';

-- Check table structure
DESCRIBE reading_tasks;

-- Check if data exists
SELECT * FROM reading_tasks;

-- Check demographics table for a sample user
SELECT u.id, u.name, u.email, d.age, d.date_of_birth 
FROM users u 
LEFT JOIN demographics d ON u.id = d.user_id 
LIMIT 5;

-- Check if any users have age information
SELECT COUNT(*) as users_with_age 
FROM demographics 
WHERE age IS NOT NULL OR date_of_birth IS NOT NULL;

-- Check total users
SELECT COUNT(*) as total_users FROM users;
