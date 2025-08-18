-- Test script to verify task11.html setup
USE dyslexia_study;

-- 1. Check if reading_tasks table exists and has data
SELECT 'Reading Tasks Table Check' as test_name;
SHOW TABLES LIKE 'reading_tasks';
SELECT COUNT(*) as total_tasks FROM reading_tasks;
SELECT id, task_name, difficulty_level, age_min, age_max FROM reading_tasks;

-- 2. Check if a specific task can be fetched
SELECT 'Specific Task Fetch Test' as test_name;
SELECT * FROM reading_tasks WHERE id = 1;

-- 3. Check user demographics for age calculation
SELECT 'User Demographics Check' as test_name;
SELECT u.id, u.name, u.email, d.age, d.date_of_birth 
FROM users u 
LEFT JOIN demographics d ON u.id = d.user_id 
LIMIT 3;

-- 4. Check if user_tasks table can be updated
SELECT 'User Tasks Table Check' as test_name;
SELECT COUNT(*) as total_user_tasks FROM user_tasks;
SELECT DISTINCT task_name FROM user_tasks;

-- 5. Test the complete flow
SELECT 'Complete Flow Test' as test_name;
-- This simulates what happens when a user starts a reading task
SELECT 
    rt.id as task_id,
    rt.task_name,
    rt.difficulty_level,
    rt.content,
    rt.instructions,
    rt.estimated_time
FROM reading_tasks rt 
WHERE rt.id = 1;
