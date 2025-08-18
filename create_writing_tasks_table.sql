-- Create writing_tasks table for age-based writing tasks
USE dyslexia_study;

CREATE TABLE IF NOT EXISTS writing_tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    task_name VARCHAR(255) NOT NULL,
    age_min INT NOT NULL,
    age_max INT NOT NULL,
    difficulty_level ENUM('Easy', 'Medium', 'Hard') NOT NULL,
    prompt TEXT NOT NULL,
    instructions TEXT,
    word_limit_min INT DEFAULT 20,
    word_limit_max INT DEFAULT 100,
    estimated_time INT DEFAULT 10,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample writing tasks for different age groups
INSERT INTO writing_tasks (task_name, age_min, age_max, difficulty_level, prompt, instructions, word_limit_min, word_limit_max, estimated_time) VALUES
('Simple Words (Ages 6-8)', 6, 8, 'Easy', 
'Write these words neatly: cat, dog, run, jump, play, book, tree, house, ball, sun', 
'Write each word clearly and carefully. Take your time to form each letter properly. Make sure your writing is easy to read.', 
10, 20, 8),

('Short Sentences (Ages 9-11)', 9, 11, 'Medium', 
'Write these sentences: "The cat runs fast." "Dogs like to play." "Birds fly high." "The sun is bright." "We read books."', 
'Write each sentence with proper spacing between words. Use capital letters at the beginning and periods at the end. Make your handwriting clear and neat.', 
20, 40, 10),

('Paragraph Writing (Ages 12-14)', 12, 14, 'Hard', 
'Write a short paragraph about your favorite hobby. Include at least 3-4 sentences explaining what you like to do and why you enjoy it.', 
'Write a complete paragraph with proper sentence structure. Use descriptive words and make sure your handwriting is legible. Include a topic sentence and supporting details.', 
40, 80, 12),

('Essay Writing (Ages 15+)', 15, 99, 'Hard', 
'Write a short essay about the importance of reading. Include an introduction, 2-3 body paragraphs with supporting points, and a conclusion.', 
'Write a well-structured essay with clear paragraphs. Use proper grammar and punctuation. Make your handwriting neat and professional. Include a thesis statement and supporting arguments.', 
80, 150, 15);

-- Create writing_samples table to store uploaded writing images
CREATE TABLE IF NOT EXISTS writing_samples (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    task_id INT NOT NULL,
    filename VARCHAR(255) NOT NULL,
    status ENUM('In Progress', 'Completed') DEFAULT 'In Progress',
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (task_id) REFERENCES writing_tasks(id) ON DELETE CASCADE
);
