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

SELECT * FROM users;
SELECT * FROM demographics;

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
DELIMITER ;

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
-- Add new columns to tasks table if they don't exist
ALTER TABLE tasks
ADD COLUMN IF NOT EXISTS instructions TEXT,
ADD COLUMN IF NOT EXISTS estimated_time VARCHAR(50),
ADD COLUMN IF NOT EXISTS devices_required VARCHAR(255),
ADD COLUMN IF NOT EXISTS example TEXT;

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
('Simple Words (Ages 6-8)', 6, 8, 'Easy', 'cat, dog, run, jump, play, book, tree, house, ball, sun, moon, star, fish, bird, car, bus', 'Read each word clearly and slowly. Take your time with each word.',5),
('Short Sentences (Ages 9-11)', 9, 11, 'Medium', 'The cat runs fast. Dogs like to play. Birds fly high in the sky. The sun is bright today. We read books together. The tree has green leaves.', 'Read each sentence with proper expression and clear pronunciation.',7),
('Paragraph Reading (Ages 12-14)', 12, 14, 'Hard', 'The little bird sat on the branch of the old oak tree. It sang a beautiful song that echoed through the quiet forest. Other animals stopped to listen to the sweet melody. The bird\'s voice was like music to their ears.', 'Read the entire paragraph fluently with good pacing and expression.',10),
('Complex Passage (Ages 15+)', 15, 99, 'Hard', 'The ancient library stood majestically at the heart of the university campus, its towering columns and intricate stone carvings telling stories of centuries past. Scholars from around the world would gather within its hallowed halls to study rare manuscripts and conduct research that would shape the future of human knowledge.', 'Read this passage with proper pacing, clear articulation, and expressive delivery.',12);


-- Create reading_comprehension_tasks table for age-based reading comprehension tasks
-- USE aviendbnew;

CREATE TABLE IF NOT EXISTS reading_comprehension_tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    task_name VARCHAR(255) NOT NULL,
    age_min INT NOT NULL,
    age_max INT NOT NULL,
    difficulty_level ENUM('Easy', 'Medium', 'Hard') NOT NULL,
    passage TEXT NOT NULL,
    question1 TEXT NOT NULL,
    question2 TEXT NOT NULL,
    question3 TEXT NOT NULL,
    answer1_options JSON,
    answer2_options JSON,
    answer3_type ENUM('text', 'multiple_choice') DEFAULT 'text',
    instructions TEXT,
    estimated_time INT DEFAULT 5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample reading comprehension tasks for different age groups
INSERT INTO reading_comprehension_tasks (task_name, age_min, age_max, difficulty_level, passage, question1, question2, question3, answer1_options, answer2_options, answer3_type, instructions, estimated_time) VALUES
('Simple Story (Ages 6-8)', 6, 8, 'Easy', 
'The little cat sat on the mat. The cat was orange and fluffy. It liked to play with a red ball. The cat would chase the ball around the house. Sometimes the ball would roll under the table. The cat would wait patiently for the ball to come back out.', 
'What color was the cat?', 
'What did the cat like to play with?', 
'Where would the ball sometimes roll?', 
'["orange", "black", "white", "brown"]', 
'["red ball", "blue toy", "green stick", "yellow rope"]', 
'text', 
'Read the story carefully and answer the questions about what happened.', 4),

('Short Story (Ages 9-11)', 9, 11, 'Medium', 
'Sarah woke up early one Saturday morning. She looked out her window and saw that it was raining. Sarah was sad because she had planned to go to the park with her friends. Her mother told her not to worry - they could play board games inside instead. Sarah and her friends had a wonderful time playing together, and Sarah learned that rainy days could be fun too.', 
'What day of the week was it?', 
'Why was Sarah sad at first?', 
'What did Sarah learn about rainy days?', 
'["Saturday", "Sunday", "Monday", "Friday"]', 
'["It was raining", "She was sick", "Her friends were busy", "She had homework"]', 
'text', 
'Read the story and answer the questions about the characters and events.', 5),

('Adventure Story (Ages 12-14)', 12, 14, 'Hard', 
'Tom and his sister Emma decided to explore the old forest behind their house. They had heard stories about a hidden cave that contained ancient treasures. Armed with a flashlight and a map they found in their grandfather\'s attic, they set off early one morning. The forest was dense and the path was overgrown, but they followed the map carefully. After hours of searching, they discovered the cave entrance hidden behind a waterfall. Inside, they found not gold or jewels, but beautiful crystals that sparkled like diamonds in the light.', 
'What did Tom and Emma want to find in the forest?', 
'How did they know where to look?', 
'What did they actually discover in the cave?', 
'["hidden cave with treasures", "wild animals", "a new path", "a river"]', 
'["map from grandfather", "GPS device", "local guide", "signs in forest"]', 
'text', 
'Read this adventure story and answer questions about the characters\' journey and discoveries.', 6),

('Complex Narrative (Ages 15+)', 15, 99, 'Hard', 
'The ancient library stood majestically at the heart of the university campus, its towering columns and intricate stone carvings telling stories of centuries past. Scholars from around the world would gather within its hallowed halls to study rare manuscripts and conduct research that would shape the future of human knowledge. Dr. Elena Rodriguez, a renowned archaeologist, had spent years searching for a particular text that was said to contain the secrets of an ancient civilization. When she finally discovered the manuscript hidden in a forgotten corner of the library\'s basement, she realized that the knowledge it contained could revolutionize our understanding of human history.', 
'What type of building is described in the passage?', 
'What was Dr. Rodriguez\'s profession?', 
'What did Dr. Rodriguez discover and what was its significance?', 
'["ancient library", "modern museum", "old church", "university building"]', 
'["archaeologist", "librarian", "historian", "professor"]', 
'text', 
'Read this complex narrative and answer questions about the setting, characters, and significance of the events described.', 7);


-- Create aptitude_tasks table for age-based aptitude tasks
CREATE TABLE IF NOT EXISTS aptitude_tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    task_name VARCHAR(255) NOT NULL,
    age_min INT NOT NULL,
    age_max INT NOT NULL,
    difficulty_level ENUM('Easy', 'Medium', 'Hard') NOT NULL,
    logical_reasoning_questions JSON,
    numerical_ability_questions JSON,
    verbal_ability_questions JSON,
    spatial_reasoning_questions JSON,
    instructions TEXT,
    estimated_time INT DEFAULT 15,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample aptitude tasks for different age groups
INSERT INTO aptitude_tasks (task_name, age_min, age_max, difficulty_level, logical_reasoning_questions, numerical_ability_questions, verbal_ability_questions, spatial_reasoning_questions, instructions, estimated_time) VALUES
('Basic Aptitude (Ages 6-8)', 6, 8, 'Easy', 
'[{"question": "If all cats are animals and Fluffy is a cat, then Fluffy is...", "options": ["an animal", "a dog", "a bird", "a fish"], "correct": 0}, {"question": "Which shape comes next: circle, square, circle, square, ?", "options": ["triangle", "circle", "square", "rectangle"], "correct": 1}]',
'[{"question": "What comes next: 2, 4, 6, 8, ?", "options": ["9", "10", "11", "12"], "correct": 1}, {"question": "If you have 3 apples and get 2 more, how many do you have?", "options": ["4", "5", "6", "7"], "correct": 1}]',
'[{"question": "Which word means the same as 'big'?", "options": ["small", "large", "tiny", "short"], "correct": 1}, {"question": "Complete: The sun is ___ in the sky", "options": ["down", "bright", "dark", "cold"], "correct": 1}]',
'[{"question": "Which shape has 3 sides?", "options": ["circle", "square", "triangle", "rectangle"], "correct": 2}, {"question": "If you fold a square in half, what shape do you get?", "options": ["circle", "triangle", "rectangle", "square"], "correct": 2}]',
'Complete each section by selecting the best answer. Take your time and think carefully about each question.', 10),

('Elementary Aptitude (Ages 9-11)', 9, 11, 'Medium',
'[{"question": "If Monday is the first day of the week and today is Wednesday, how many days until the weekend?", "options": ["2", "3", "4", "5"], "correct": 1}, {"question": "Which pattern continues: A, B, C, A, B, C, ?", "options": ["A", "B", "C", "D"], "correct": 0}]',
'[{"question": "What is 15 + 27?", "options": ["40", "42", "43", "44"], "correct": 1}, {"question": "If a book costs $8 and you have $20, how much change will you get?", "options": ["$10", "$11", "$12", "$13"], "correct": 2}]',
'[{"question": "What is the opposite of 'happy'?", "options": ["sad", "excited", "calm", "angry"], "correct": 0}, {"question": "Which word fits: The weather is ___ today", "options": ["quickly", "beautiful", "run", "happy"], "correct": 1}]',
'[{"question": "How many faces does a cube have?", "options": ["4", "6", "8", "12"], "correct": 1}, {"question": "If you rotate a triangle 180 degrees, what happens?", "options": ["It gets bigger", "It flips upside down", "It disappears", "Nothing"], "correct": 1}]',
'Work through each section systematically. Read each question carefully and choose the most logical answer.', 15),

('Intermediate Aptitude (Ages 12-14)', 12, 14, 'Hard',
'[{"question": "If all roses are flowers and some flowers are red, then:", "options": ["All roses are red", "Some roses might be red", "No roses are red", "All red things are roses"], "correct": 1}, {"question": "Complete the sequence: 2, 6, 12, 20, ?", "options": ["28", "30", "32", "34"], "correct": 1}]',
'[{"question": "What is 3/4 of 80?", "options": ["50", "60", "70", "80"], "correct": 1}, {"question": "If a train travels 120 km in 2 hours, what is its speed?", "options": ["40 km/h", "60 km/h", "80 km/h", "120 km/h"], "correct": 1}]',
'[{"question": "What is a synonym for 'enormous'?", "options": ["tiny", "huge", "small", "medium"], "correct": 1}, {"question": "Which sentence is grammatically correct?", "options": ["Me and him went to the store", "Him and I went to the store", "He and I went to the store", "I and he went to the store"], "correct": 2}]',
'[{"question": "How many edges does a triangular prism have?", "options": ["6", "9", "12", "15"], "correct": 1}, {"question": "If you fold a piece of paper in half 3 times, how many layers will you have?", "options": ["6", "8", "9", "12"], "correct": 1}]',
'This is a comprehensive aptitude assessment. Take your time with each question and use logical reasoning.', 20),

('Advanced Aptitude (Ages 15+)', 15, 99, 'Hard',
'[{"question": "If no artists are engineers and some engineers are scientists, then:", "options": ["Some artists are scientists", "No artists are scientists", "All scientists are artists", "Cannot be determined"], "correct": 3}, {"question": "Find the next number: 1, 3, 7, 15, 31, ?", "options": ["47", "63", "65", "67"], "correct": 1}]',
'[{"question": "What is 25% of 3/5?", "options": ["3/20", "3/25", "15/100", "3/4"], "correct": 0}, {"question": "If x + y = 10 and xy = 24, what is x² + y²?", "options": ["52", "76", "100", "124"], "correct": 0}]',
'[{"question": "What is the meaning of 'ubiquitous'?", "options": ["rare", "everywhere", "expensive", "beautiful"], "correct": 1}, {"question": "Which word is an antonym of 'benevolent'?", "options": ["kind", "generous", "malevolent", "charitable"], "correct": 2}]',
'[{"question": "How many different ways can you arrange 4 books on a shelf?", "options": ["12", "16", "24", "32"], "correct": 2}, {"question": "If you have a 3x3x3 cube and paint all faces, how many small cubes have exactly 2 painted faces?", "options": ["6", "12", "18", "24"], "correct": 1}]',
'This advanced aptitude test requires careful analysis and logical thinking. Consider all options before answering.', 25);

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

-- Clean up any old incomplete task records first
DELETE FROM tasks WHERE task_name IN ('Reading Aloud Task 1', 'Typing Task', 'Reading Comprehension') AND (instructions IS NULL OR estimated_time IS NULL);

-- Insert or update all core tasks
INSERT INTO tasks (task_name, description, instructions, estimated_time, devices_required, example) VALUES
('Reading Aloud Task 1', 'Read the given passage aloud and record your voice.', 'Read the passage clearly and at a comfortable pace. Record your voice while reading.', '5-10 minutes', 'Computer with microphone', 'Sample passage: "The quick brown fox jumps over the lazy dog."'),
('Typing Task', 'Type an essay on the given topic.', 'Type your response to the given prompt. Focus on accuracy and speed.', '15-20 minutes', 'Computer with keyboard', 'Sample prompt: "Write about your favorite hobby."'),
('Reading Comprehension', 'Answer questions based on the given passage.', 'Read the passage carefully and answer the comprehension questions.', '10-15 minutes', 'Computer with internet connection', 'Sample question: "What is the main idea of the passage?"'),
('Mathematical Comprehension', 'Solve math-based comprehension questions.', 'Read the math problem and solve the questions step by step.', '15-20 minutes', 'Computer with internet connection', 'Sample problem: "If you have 5 apples and give away 2, how many do you have left?"'),
('Writing Task', 'Write a creative story or essay as instructed.', 'Write a response to the given prompt. Be creative and express your ideas clearly.', '20-30 minutes', 'Computer with keyboard', 'Sample prompt: "Write a short story about a magical adventure."'),
('Aptitude Test', 'Comprehensive aptitude assessment covering logical reasoning, numerical ability, verbal ability, and spatial reasoning', 'Complete all four sections of the aptitude test. Each section contains multiple-choice questions. You can save your progress and return later.', '45-60 minutes', 'Computer with internet connection', 'Sample question: What comes next in the sequence 2, 4, 8, 16, ?')
ON DUPLICATE KEY UPDATE 
    description = VALUES(description),
    instructions = VALUES(instructions),
    estimated_time = VALUES(estimated_time),
    devices_required = VALUES(devices_required),
    example = VALUES(example);


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

CREATE TABLE IF NOT EXISTS mathematical_comprehension_tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    task_name VARCHAR(255) NOT NULL,
    age_min INT NOT NULL,
    age_max INT NOT NULL,
    difficulty_level ENUM('Easy', 'Medium', 'Hard') NOT NULL,
    problem_text TEXT NOT NULL,
    question1 TEXT NOT NULL,
    question2 TEXT NOT NULL,
    question3 TEXT NOT NULL,
    answer1_options JSON,
    answer2_options JSON,
    answer3_type ENUM('number', 'text', 'multiple_choice') DEFAULT 'number',
    instructions TEXT,
    estimated_time INT DEFAULT 5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample mathematical comprehension tasks for different age groups
INSERT INTO mathematical_comprehension_tasks (task_name, age_min, age_max, difficulty_level, problem_text, question1, question2, question3, answer1_options, answer2_options, answer3_type, instructions, estimated_time) VALUES
('Simple Counting (Ages 6-8)', 6, 8, 'Easy', 
'Tom has 5 red apples and 3 green apples. His friend Sarah gives him 2 more red apples. Tom wants to share all his apples equally with his sister Emma.', 
'How many red apples does Tom have now?', 
'How many total apples does Tom have?', 
'How many apples will Tom and Emma each get if they share equally?', 
'["5", "6", "7", "8"]', 
'["8", "9", "10", "11"]', 
'number', 
'Read the problem carefully and solve the math questions. Use counting and simple addition.', 4),

('Money Problems (Ages 9-11)', 9, 11, 'Medium', 
'A toy store sells action figures for $8 each and board games for $15 each. On Saturday, they sold 6 action figures and 3 board games. The store also had a sale where customers got $2 off each item if they bought 3 or more things.', 
'How much money did the store make from action figures?', 
'How much money did the store make from board games?', 
'How much total money did the store make on Saturday?', 
'["$40", "$42", "$48", "$50"]', 
'["$40", "$42", "$45", "$48"]', 
'number', 
'Read the problem carefully and solve the money questions. Remember to calculate discounts.', 5),

('Fraction Story (Ages 12-14)', 12, 14, 'Hard', 
'A pizza restaurant makes large pizzas that are cut into 12 slices. On Friday night, they sold 8 whole pizzas and 3/4 of another pizza. Each slice costs $2.50. The restaurant also had a special: buy 2 whole pizzas and get 1/2 pizza free.', 
'How many slices were sold in total?', 
'How much money did the restaurant make from the slices sold?', 
'If a customer bought 2 whole pizzas and got the special deal, how many slices would they have?', 
'["96", "99", "102", "105"]', 
'["$240", "$247.50", "$255", "$262.50"]', 
'number', 
'Read the problem carefully and solve the fraction and money questions. Pay attention to the special deal.', 6),

('Complex Business Math (Ages 15+)', 15, 99, 'Hard', 
'A coffee shop has fixed costs of $2,000 per month (rent, utilities, etc.) and variable costs of $1.50 per coffee sold. They sell coffee for $4.50 each. Last month, they sold 800 coffees. The shop also offers a loyalty program where customers get 1 free coffee for every 10 purchased.', 
'What were the total costs for the shop last month?', 
'How much profit did the shop make last month?', 
'If the shop wants to make $3,000 profit next month, how many coffees do they need to sell?', 
'["$3,200", "$3,400", "$3,600", "$3,800"]', 
'["$400", "$600", "$800", "$1,000"]', 
'number', 
'Read the problem carefully and solve the business math questions. Consider fixed costs, variable costs, and revenue.', 7);

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


USE dyslexia_study;
SELECT * from tasks;
SELECT * FROM user_tasks;
SELECT * FROM users;
SELECT * FROM schools;
SELECT * FROM school_parents;
SELECT * FROM parent_children;
SELECT * FROM consent_data;
SELECT * FROM demographics;

TRUNCATE TABLE users;
TRUNCATE TABLE schools;
TRUNCATE TABLE school_parents;
TRUNCATE TABLE parent_children;

delete from users;

 SELECT * FROM SCHOOL_PARENTS;
-- SELECT * from tasks;
-- SELECT * FROM user_tasks WHERE user_id = 5;
-- Show table structure
-- DESCRIBE users;
-- DESCRIBE consent_data;
-- DESCRIBE demographics;

-- DELETE FROM AUDIO_RECORDINGS WHERE user_id = 2;
-- SELECT * FROM user_tasks;
-- SELECT * FROM AUDIO_RECORDINGS;
-- SELECT * FROM TYPING_PROGRESS;
-- SELECT * FROM users;
-- SELECT * FROM consent_data;
-- SELECT * FROM demographics;

-- DROP DATABASE IF EXISTS dyslexia_study;
-- select * from  parent_children ;