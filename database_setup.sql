-- Create the database
CREATE DATABASE IF NOT EXISTS dyslexia_study;
USE dyslexia_study;

-- Create schools table
CREATE TABLE IF NOT EXISTS schools (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    address TEXT,
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Create users table (for parents and children)
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    is_18_or_above BOOLEAN NOT NULL,
    user_type ENUM('parent', 'child', 'participant') DEFAULT 'participant',
    school_id INT DEFAULT NULL,
    parent_id INT DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (school_id) REFERENCES schools(id) ON DELETE SET NULL,
    FOREIGN KEY (parent_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Create school_parents table to track school-parent relationships
CREATE TABLE IF NOT EXISTS school_parents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    school_id INT NOT NULL,
    parent_id INT NOT NULL,
    added_by_school BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (school_id) REFERENCES schools(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_school_parent (school_id, parent_id)
);

-- Create parent_children table to track parent-child relationships
CREATE TABLE IF NOT EXISTS parent_children (
    id INT AUTO_INCREMENT PRIMARY KEY,
    parent_id INT NOT NULL,
    child_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (child_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_parent_child (parent_id, child_id)
);

-- Create consent table to store consent data
CREATE TABLE IF NOT EXISTS consent_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    consent_given BOOLEAN DEFAULT FALSE,
    consent_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),
    user_agent TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create demographics table to store profile setup data
CREATE TABLE IF NOT EXISTS demographics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    date_of_birth DATE,
    age INT,
    gender VARCHAR(20),
    native_language VARCHAR(100),
    education_level VARCHAR(100),
    dyslexia_status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create user_tasks table to track each user's task status (Not Started, In Progress, Completed) for each task
CREATE TABLE IF NOT EXISTS user_tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    task_name VARCHAR(100) NOT NULL,
    status ENUM('Not Started', 'In Progress', 'Completed') DEFAULT 'Not Started',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_task (user_id, task_name)
);

-- Create audio_recordings table to store uploaded audio files
CREATE TABLE IF NOT EXISTS audio_recordings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    filename VARCHAR(255) NOT NULL,
    task_name VARCHAR(100) DEFAULT 'Reading Aloud Task 1',
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Trigger to auto-calculate age from date_of_birth
DELIMITER $$
CREATE TRIGGER set_age_before_insert
BEFORE INSERT ON demographics
FOR EACH ROW
BEGIN
    IF NEW.date_of_birth IS NOT NULL THEN
        SET NEW.age = TIMESTAMPDIFF(YEAR, NEW.date_of_birth, CURDATE());
    END IF;
END$$
-- DELIMITER ;

DELIMITER $$
CREATE TRIGGER set_age_before_update
BEFORE UPDATE ON demographics
FOR EACH ROW
BEGIN
    IF NEW.date_of_birth IS NOT NULL THEN
        SET NEW.age = TIMESTAMPDIFF(YEAR, NEW.date_of_birth, CURDATE());
    END IF;
END$$
DELIMITER ;

CREATE TABLE typing_progress (
    user_id INT NOT NULL,
    text TEXT,
    keystrokes LONGTEXT,
    timer INT,
    updated_at DATETIME,
    PRIMARY KEY (user_id)
);

CREATE TABLE IF NOT EXISTS comprehension_progress (
    user_id INT PRIMARY KEY,
    q1 TEXT,
    q2 VARCHAR(255),
    q3 TEXT,
    status ENUM('In Progress', 'Completed') DEFAULT 'In Progress',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    task_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO tasks (task_name, description) VALUES
  ('Reading Aloud Task 1', 'Read the given passage aloud and record your voice.'),
  ('Typing Task', 'Type an essay on the given topic.'),
  ('Reading Comprehension', 'Answer questions based on the given passage.');
ALTER TABLE tasks
ADD COLUMN instructions TEXT,
ADD COLUMN estimated_time VARCHAR(50),
ADD COLUMN devices_required VARCHAR(255),
ADD COLUMN example TEXT;

-- Sample data for testing
-- Insert a sample school
INSERT INTO schools (name, email, password_hash, address, phone) VALUES
('Sample School', 'school@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.i8eO', '123 School Street, City', '555-0123');

-- Insert sample parents linked to the school
INSERT INTO users (name, email, password_hash, is_18_or_above, user_type, school_id) VALUES
('John Parent', 'parent1@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.i8eO', TRUE, 'parent', 1),
('Jane Parent', 'parent2@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.i8eO', TRUE, 'parent', 1);

-- Link parents to school
INSERT INTO school_parents (school_id, parent_id) VALUES
(1, 1),
(1, 2);

-- Insert sample children linked to parents
INSERT INTO users (name, email, password_hash, is_18_or_above, user_type, parent_id) VALUES
('Child One', 'child1@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.i8eO', TRUE, 'child', 1),
('Child Two', 'child2@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.i8eO', TRUE, 'child', 2);

-- Link children to parents
INSERT INTO parent_children (parent_id, child_id) VALUES
(1, 3),
(2, 4);

USE dyslexia_study;
SELECT * from tasks;
SELECT * FROM user_tasks;
SELECT * FROM users;
SELECT * FROM schools;
SELECT * FROM school_parents;
SELECT * FROM parent_children;


