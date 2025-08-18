# Quick Fix Guide - Reading Tasks Not Working

## The Problem
You're seeing "something went wrong" instead of reading tasks. This usually means one of these issues:

1. **Database table missing** - The `reading_tasks` table doesn't exist
2. **No user age data** - User hasn't completed profile setup
3. **Database connection issues** - Can't connect to MySQL

## Quick Fix Steps

### Step 1: Check Database Setup
Run this in your MySQL database:
```sql
USE dyslexia_study;
SHOW TABLES LIKE 'reading_tasks';
```

If the table doesn't exist, run:
```sql
source create_reading_tasks_table.sql;
```

### Step 2: Verify Data Exists
```sql
SELECT * FROM reading_tasks;
```

You should see 4 tasks for different age groups.

### Step 3: Check User Profile
```sql
-- Check if any users have age data
SELECT u.id, u.name, d.age, d.date_of_birth 
FROM users u 
LEFT JOIN demographics d ON u.id = d.user_id 
LIMIT 5;
```

### Step 4: Test the API
1. **Restart your Flask app** after making changes
2. **Check browser console** for error messages
3. **Check Flask console** for backend error messages

## Common Issues & Solutions

### Issue 1: "reading_tasks table doesn't exist"
**Solution**: Run the database setup script
```sql
source create_reading_tasks_table.sql;
```

### Issue 2: "No demographics found"
**Solution**: User needs to complete profile setup
- Go to `/profile-setup`
- Fill in date of birth
- Save profile

### Issue 3: "Database connection failed"
**Solution**: Check your MySQL connection
- Verify MySQL is running
- Check database credentials in app.py
- Test connection manually

### Issue 4: "No reading tasks found for age X"
**Solution**: Check age ranges in reading_tasks table
```sql
SELECT age_min, age_max, task_name FROM reading_tasks;
```

## Testing the Fix

1. **Complete database setup**
2. **Restart Flask app**
3. **Log in as a user with age data**
4. **Navigate to `/task1.html`**
5. **Check browser console for any errors**

## Debug Information

The updated code now includes:
- **Better error messages** - More specific error details
- **Fallback tasks** - Shows all tasks if age not available
- **Console logging** - Check browser console for details
- **Database debugging** - Check Flask console for backend errors

## Still Not Working?

If you're still having issues:

1. **Check Flask console** for error messages
2. **Check browser console** for JavaScript errors  
3. **Verify database connection** with simple queries
4. **Check user authentication** - make sure user is logged in

## Quick Test Commands

```sql
-- Test database connection
USE dyslexia_study;
SELECT 1;

-- Test reading_tasks table
SELECT COUNT(*) FROM reading_tasks;

-- Test user demographics
SELECT COUNT(*) FROM demographics WHERE age IS NOT NULL;
```
