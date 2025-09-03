#!/usr/bin/env python3

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

def create_table():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Create mathematical comprehension progress table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mathematical_comprehension_progress (
                user_id INT PRIMARY KEY,
                q1 TEXT,
                q2 VARCHAR(255),
                q3 TEXT,
                status ENUM('In Progress', 'Completed') DEFAULT 'In Progress',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        conn.commit()
        print("✅ Mathematical comprehension progress table created successfully!")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error creating table: {e}")

if __name__ == "__main__":
    create_table() 