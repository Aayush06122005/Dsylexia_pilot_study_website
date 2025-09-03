-- Create mathematical comprehension progress table
USE dyslexia_study;

CREATE TABLE IF NOT EXISTS mathematical_comprehension_progress (
    user_id INT PRIMARY KEY,
    q1 TEXT,
    q2 VARCHAR(255),
    q3 TEXT,
    status ENUM('In Progress', 'Completed') DEFAULT 'In Progress',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
); 