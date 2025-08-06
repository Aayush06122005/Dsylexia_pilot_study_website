USE dyslexia_study;

-- Create audio_recordings table to store uploaded audio files
CREATE TABLE IF NOT EXISTS audio_recordings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    filename VARCHAR(255) NOT NULL,
    task_name VARCHAR(100) DEFAULT 'Reading Aloud Task 1',
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
); 