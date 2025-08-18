#!/usr/bin/env python3
"""
Test script to check database tasks and debug dashboard issues
"""

import mysql.connector
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DB_CONFIG = {
    "host": os.getenv("MYSQLHOST", "localhost"),
    "user": os.getenv("MYSQLUSER", "root"),
    "password": os.getenv("MYSQLPASSWORD", ""),
    "database": os.getenv("MYSQLDATABASE", "dyslexia_study"),
    "port": int(os.getenv("MYSQLPORT", 3306))
}

def test_database():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        print("=== Database Connection Test ===")
        print(f"Connected to: {DB_CONFIG['database']}")
        print()
        
        # Check if tasks table exists
        cursor.execute("SHOW TABLES LIKE 'tasks'")
        if cursor.fetchone():
            print("✅ Tasks table exists")
        else:
            print("❌ Tasks table does not exist")
            return
        
        # Check tasks table structure
        print("\n=== Tasks Table Structure ===")
        cursor.execute("DESCRIBE tasks")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  {col['Field']}: {col['Type']} {'NULL' if col['Null'] == 'YES' else 'NOT NULL'}")
        
        # Check all tasks in the table
        print("\n=== All Tasks in Database ===")
        cursor.execute("SELECT * FROM tasks ORDER BY id")
        tasks = cursor.fetchall()
        
        if tasks:
            for task in tasks:
                print(f"  ID: {task['id']}")
                print(f"  Name: '{task['task_name']}'")
                print(f"  Description: {task.get('description', 'NULL')}")
                print(f"  Instructions: {task.get('instructions', 'NULL')}")
                print(f"  Estimated Time: {task.get('estimated_time', 'NULL')}")
                print(f"  Devices Required: {task.get('devices_required', 'NULL')}")
                print(f"  Example: {task.get('example', 'NULL')}")
                print(f"  Created: {task.get('created_at', 'NULL')}")
                print("  ---")
        else:
            print("  No tasks found in database")
        
        # Check user_tasks table
        print("\n=== User Tasks Table ===")
        cursor.execute("SHOW TABLES LIKE 'user_tasks'")
        if cursor.fetchone():
            print("✅ User_tasks table exists")
            
            # Check if there are any users
            cursor.execute("SELECT COUNT(*) as count FROM users")
            user_count = cursor.fetchone()['count']
            print(f"  Total users: {user_count}")
            
            if user_count > 0:
                # Get first user's tasks
                cursor.execute("SELECT * FROM user_tasks LIMIT 5")
                user_tasks = cursor.fetchall()
                if user_tasks:
                    print("  Sample user tasks:")
                    for ut in user_tasks:
                        print(f"    User {ut['user_id']}: {ut['task_name']} - {ut['status']}")
                else:
                    print("  No user tasks found")
        else:
            print("❌ User_tasks table does not exist")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_database()
