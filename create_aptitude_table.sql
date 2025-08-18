-- Create aptitude_progress table for storing aptitude task data
USE dyslexia_study;

CREATE TABLE IF NOT EXISTS aptitude_progress (
    user_id INT PRIMARY KEY,
    logical_reasoning_score INT DEFAULT 0,
    numerical_ability_score INT DEFAULT 0,
    verbal_ability_score INT DEFAULT 0,
    spatial_reasoning_score INT DEFAULT 0,
    total_score INT DEFAULT 0,
    status ENUM('In Progress', 'Completed') DEFAULT 'In Progress',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

