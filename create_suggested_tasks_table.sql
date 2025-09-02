-- SQL to create the suggested_tasks table
CREATE TABLE IF NOT EXISTS suggested_tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    school_id INT NOT NULL,
    task_name VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    description TEXT,
    estimated_time INT,
    devices_required VARCHAR(255),
    details TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (school_id) REFERENCES schools(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


