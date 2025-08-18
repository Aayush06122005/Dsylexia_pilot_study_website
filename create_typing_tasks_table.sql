-- Create typing_tasks table for age-based typing tasks
USE dyslexia_study;

CREATE TABLE IF NOT EXISTS typing_tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    task_name VARCHAR(255) NOT NULL,
    age_min INT NOT NULL,
    age_max INT NOT NULL,
    difficulty_level ENUM('Easy', 'Medium', 'Hard') NOT NULL,
    prompt TEXT NOT NULL,
    instructions TEXT,
    word_limit_min INT DEFAULT 50,
    word_limit_max INT DEFAULT 200,
    estimated_time INT DEFAULT 10,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample typing tasks for different age groups
INSERT INTO typing_tasks (task_name, age_min, age_max, difficulty_level, prompt, instructions, word_limit_min, word_limit_max, estimated_time) VALUES
('Simple Sentences (Ages 6-8)', 6, 8, 'Easy', 
'Write about your favorite animal. Tell us what it looks like and why you like it.', 
'Type simple sentences about your favorite animal. Use words you know how to spell. Try to write at least 3-4 sentences.', 
30, 80, 8),

('Short Story (Ages 9-11)', 9, 11, 'Medium', 
'Write a short story about a magical day. What would happen if you woke up one morning and found you had a special power?', 
'Write a short story with a beginning, middle, and end. Include characters and describe what happens. Try to make it interesting!', 
80, 150, 12),

('Personal Essay (Ages 12-14)', 12, 14, 'Hard', 
'Write an essay about a challenge you faced and how you overcame it. What did you learn from this experience?', 
'Write a well-structured essay with an introduction, body paragraphs, and conclusion. Use descriptive language and explain your thoughts clearly.', 
150, 300, 15),

('Analytical Writing (Ages 15+)', 15, 99, 'Hard', 
'Write an essay discussing the impact of technology on modern education. Consider both positive and negative effects, and provide examples to support your arguments.', 
'Write a formal essay with a clear thesis statement, well-developed arguments, and supporting evidence. Use academic language and proper essay structure.', 
250, 500, 20);
