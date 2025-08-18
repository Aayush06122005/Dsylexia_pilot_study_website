-- Create reading_tasks table for age-based reading tasks
USE dyslexia_study;

CREATE TABLE IF NOT EXISTS reading_tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    task_name VARCHAR(255) NOT NULL,
    age_min INT NOT NULL,
    age_max INT NOT NULL,
    difficulty_level ENUM('Easy', 'Medium', 'Hard') NOT NULL,
    content TEXT NOT NULL,
    instructions TEXT,
    estimated_time INT DEFAULT 5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample reading tasks for different age groups
INSERT INTO reading_tasks (task_name, age_min, age_max, difficulty_level, content, instructions, estimated_time) VALUES
('Simple Words (Ages 6-8)', 6, 8, 'Easy', 'cat, dog, run, jump, play, book, tree, house, ball, sun, moon, star, fish, bird, car, bus', 'Read each word clearly and slowly. Take your time with each word.'),
('Short Sentences (Ages 9-11)', 9, 11, 'Medium', 'The cat runs fast. Dogs like to play. Birds fly high in the sky. The sun is bright today. We read books together. The tree has green leaves.', 'Read each sentence with proper expression and clear pronunciation.'),
('Paragraph Reading (Ages 12-14)', 12, 14, 'Hard', 'The little bird sat on the branch of the old oak tree. It sang a beautiful song that echoed through the quiet forest. Other animals stopped to listen to the sweet melody. The bird\'s voice was like music to their ears.', 'Read the entire paragraph fluently with good pacing and expression.'),
('Complex Passage (Ages 15+)', 15, 99, 'Hard', 'The ancient library stood majestically at the heart of the university campus, its towering columns and intricate stone carvings telling stories of centuries past. Scholars from around the world would gather within its hallowed halls to study rare manuscripts and conduct research that would shape the future of human knowledge.', 'Read this passage with proper pacing, clear articulation, and expressive delivery.');

