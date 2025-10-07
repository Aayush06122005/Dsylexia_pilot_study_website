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
ALTER TABLE users 
ADD COLUMN class VARCHAR(50) DEFAULT NULL;

-- Add academic year and class tracking
ALTER TABLE users 
ADD COLUMN academic_year INT DEFAULT NULL,
ADD INDEX idx_class_year (class, academic_year);

-- Extend users to support section membership and activation state
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS section_id INT NULL,
ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS pending_parent_email VARCHAR(255) NULL,
ADD FOREIGN KEY (section_id) REFERENCES class_sections(id) ON DELETE SET NULL;

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

CREATE TABLE IF NOT EXISTS audio_recordings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    attempt_id INT NOT NULL,
    filename VARCHAR(255) NOT NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (attempt_id) REFERENCES user_task_attempts(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS typing_progress (
    id INT AUTO_INCREMENT PRIMARY KEY,
    attempt_id INT NOT NULL,
    text TEXT,
    keystrokes LONGTEXT,
    timer INT,
    updated_at DATETIME,
    FOREIGN KEY (attempt_id) REFERENCES user_task_attempts(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS comprehension_progress (
    id INT AUTO_INCREMENT PRIMARY KEY,
    attempt_id INT NOT NULL,
    q1 TEXT,
    q2 VARCHAR(255),
    q3 TEXT,
    status ENUM('In Progress', 'Completed') DEFAULT 'In Progress',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (attempt_id) REFERENCES user_task_attempts(id) ON DELETE CASCADE
);

-- Create aptitude_progress table for storing aptitude task data
CREATE TABLE IF NOT EXISTS aptitude_progress (
    id INT AUTO_INCREMENT PRIMARY KEY,
    attempt_id INT NOT NULL,
    logical_reasoning_score INT DEFAULT 0,
    numerical_ability_score INT DEFAULT 0,
    verbal_ability_score INT DEFAULT 0,
    spatial_reasoning_score INT DEFAULT 0,
    total_score INT DEFAULT 0,
    status ENUM('In Progress', 'Completed') DEFAULT 'In Progress',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (attempt_id) REFERENCES user_task_attempts(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS writing_samples (
    id INT AUTO_INCREMENT PRIMARY KEY,
    attempt_id INT NOT NULL,
    filename VARCHAR(255) NOT NULL,
    status ENUM('In Progress', 'Completed') DEFAULT 'In Progress',
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (attempt_id) REFERENCES user_task_attempts(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS mathematical_comprehension_progress (
    id INT AUTO_INCREMENT PRIMARY KEY,
    attempt_id INT NOT NULL,
    q1 TEXT,
    q2 TEXT,
    q3 TEXT,
    status ENUM('In Progress', 'Completed') DEFAULT 'In Progress',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (attempt_id) REFERENCES user_task_attempts(id) ON DELETE CASCADE
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

CREATE TABLE IF NOT EXISTS reading_tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    task_name VARCHAR(255) NOT NULL,
	class_level INT NOT NULL CHECK (class_level BETWEEN 1 AND 12),
    difficulty_level ENUM('Easy', 'Medium', 'Hard') NOT NULL,
    content TEXT NOT NULL,
    instructions TEXT,
    estimated_time INT DEFAULT 5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO reading_tasks (task_name, class_level, difficulty_level, content, instructions, estimated_time) VALUES
('Reading Task - Class 1', 1, 'Easy', 'cat, dog, sun, run, ball, book, car', 'Read each word clearly and repeat it aloud.', 4),
('Reading Task - Class 2', 2, 'Easy', 'The cat jumps. The sun is bright. We play outside.', 'Read each sentence with expression.', 5),
('Reading Task - Class 3', 3, 'Medium', 'Tom likes to read books. He has a red ball and a brown dog.', 'Read slowly and clearly.', 6),
('Reading Task - Class 4', 4, 'Medium', 'The little bird sings on the tree. It is a sunny morning.', 'Read the paragraph with correct pauses.', 6),
('Reading Task - Class 5', 5, 'Medium', 'A farmer works hard in the field every day. He grows food for everyone.', 'Read fluently and emphasize important words.', 7),
('Reading Task - Class 6', 6, 'Medium', 'The river flowed quietly through the village as children played on its banks.', 'Read naturally, maintaining flow and tone.', 8),
('Reading Task - Class 7', 7, 'Hard', 'The mountains were covered with snow, and the wind howled through the valley.', 'Read with confidence and emotion.', 9),
('Reading Task - Class 8', 8, 'Hard', 'In ancient times, people built magnificent temples and monuments using simple tools.', 'Read the passage with clarity and pacing.', 10),
('Reading Task - Class 9', 9, 'Hard', 'The invention of the printing press revolutionized human communication.', 'Focus on pronunciation and fluency.', 10),
('Reading Task - Class 10', 10, 'Hard', 'The discovery of gravity changed the way we understand the universe.', 'Read with proper tone and phrasing.', 11),
('Reading Task - Class 11', 11, 'Hard', 'The global economy thrives on innovation, creativity, and sustainable practices.', 'Maintain clear pronunciation and confidence.', 12),
('Reading Task - Class 12', 12, 'Hard', 'The rise of artificial intelligence has reshaped industries and human lifestyles.', 'Read in an academic and expressive tone.', 12);

CREATE TABLE IF NOT EXISTS reading_comprehension_tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    task_name VARCHAR(255) NOT NULL,
    class_level INT NOT NULL CHECK (class_level BETWEEN 1 AND 12),
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

INSERT INTO reading_comprehension_tasks (task_name, class_level, difficulty_level, passage, question1, question2, question3, answer1_options, answer2_options, answer3_type, instructions, estimated_time) VALUES
('Comprehension - Class 1', 1, 'Easy', 'The cat sat on the mat.', 'Who sat on the mat?', 'What animal is in the story?', 'Where was the cat?', '["cat","dog","bird","fish"]', '["mat","tree","chair","car"]', 'text', 'Read the short story and answer simple questions.', 4),
('Comprehension - Class 2', 2, 'Easy', 'A boy has a red kite. He flies it in the park.', 'What color is the kite?', 'Where does he fly it?', 'Who has the kite?', '["red","blue","green","yellow"]', '["school","home","park","beach"]', 'text', 'Read and answer the questions.', 4),
('Comprehension - Class 3', 3, 'Medium', 'Lina likes to draw. She paints flowers and animals.', 'What does Lina like to do?', 'What does she paint?', 'Is she good at it?', '["draw","dance","read","cook"]', '["flowers","cars","houses","toys"]', 'text', 'Read carefully and answer the questions.', 5),
('Comprehension - Class 4', 4, 'Medium', 'Ravi planted a tree. It grew tall and gave shade.', 'Who planted the tree?', 'What did the tree give?', 'Was Ravi happy?', '["Ravi","Mina","Amit","Sara"]', '["shade","fruit","wood","flowers"]', 'text', 'Read the passage and answer logically.', 5),
('Comprehension - Class 5', 5, 'Medium', 'The river near the village helps farmers grow crops.', 'Where is the river?', 'Who uses the river?', 'What do they grow?', '["near village","mountain","forest","city"]', '["farmers","teachers","doctors","students"]', 'text', 'Read and answer based on context.', 6),
('Comprehension - Class 6', 6, 'Medium', 'The Sun gives us light and warmth, helping plants grow.', 'What does the Sun give?', 'How does it help plants?', 'Why is it important?', '["light","food","rain","wind"]', '["helps grow","stops growth","hurts","freezes"]', 'text', 'Understand and explain clearly.', 6),
('Comprehension - Class 7', 7, 'Hard', 'Electricity changed how people lived and worked.', 'What changed people\'s lives?', 'How did it help?', 'When did it happen?', '["electricity","internet","fire","radio"]', '["made life easy","made life hard","no change","none"]', 'text', 'Focus on meaning and main idea.', 7),
('Comprehension - Class 8', 8, 'Hard', 'The Wright brothers built the first successful airplane in 1903.', 'Who built it?', 'When was it built?', 'What did they build?', '["Wright brothers","Newton","Edison","Tesla"]', '["1900","1903","1910","1920"]', 'text', 'Identify details and key facts.', 8),
('Comprehension - Class 9', 9, 'Hard', 'Mahatma Gandhi led India to freedom through non-violence.', 'Who led India to freedom?', 'What method did he use?', 'What did it achieve?', '["Gandhi","Nehru","Bose","Patel"]', '["non-violence","war","rebellion","law"]', 'text', 'Comprehend and interpret ideas.', 9),
('Comprehension - Class 10', 10, 'Hard', 'The Industrial Revolution transformed global economies and societies.', 'What was transformed?', 'What caused it?', 'How did it change society?', '["economies","nature","religion","art"]', '["industrial revolution","internet","trade","wars"]', 'text', 'Focus on cause and effect.', 10),
('Comprehension - Class 11', 11, 'Hard', 'Climate change is a major challenge caused by human activity.', 'What is the challenge?', 'Who causes it?', 'How can we fix it?', '["climate change","pollution","traffic","drought"]', '["humans","animals","plants","machines"]', 'text', 'Analyze and explain critically.', 10),
('Comprehension - Class 12', 12, 'Hard', 'Artificial intelligence impacts industries, education, and society.', 'What impacts industries?', 'Where else is it used?', 'What are its effects?', '["AI","ML","robots","data"]', '["education","sports","music","space"]', 'text', 'Interpret complex text meaningfully.', 12);

-- Create aptitude_tasks table for age-based aptitude tasks
CREATE TABLE IF NOT EXISTS aptitude_tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    task_name VARCHAR(255) NOT NULL,
	class_level INT NOT NULL CHECK (class_level BETWEEN 1 AND 12),
    difficulty_level ENUM('Easy', 'Medium', 'Hard') NOT NULL,
    logical_reasoning_questions JSON,
    numerical_ability_questions JSON,
    verbal_ability_questions JSON,
    spatial_reasoning_questions JSON,
    instructions TEXT,
    estimated_time INT DEFAULT 15,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO aptitude_tasks (task_name, class_level, difficulty_level, logical_reasoning_questions, numerical_ability_questions, verbal_ability_questions, spatial_reasoning_questions, instructions, estimated_time) VALUES
('Aptitude - Class 1', 1, 'Easy', '[{"q":"If sun is day, moon is ___","a":"night"}]', '[{"q":"2+2=?","a":"4"}]', '[{"q":"Opposite of hot?","a":"cold"}]', '[{"q":"Which shape has 3 sides?","a":"triangle"}]', 'Answer simple reasoning questions.', 5),
('Aptitude - Class 2', 2, 'Easy', '[{"q":"If all cats are animals, Fluffy is a cat. Fluffy is?","a":"animal"}]', '[{"q":"3+5=?","a":"8"}]', '[{"q":"Synonym of big?","a":"large"}]', '[{"q":"Square has how many corners?","a":"4"}]', 'Think and choose the correct answer.', 6),
('Aptitude - Class 3', 3, 'Medium', '[{"q":"Find odd one: cat, dog, fish, tree","a":"tree"}]', '[{"q":"10-6=?","a":"4"}]', '[{"q":"Opposite of fast?","a":"slow"}]', '[{"q":"Triangle has how many angles?","a":"3"}]', 'Solve basic logic and math problems.', 7),
('Aptitude - Class 4', 4, 'Medium', '[{"q":"If A=1, B=2, then C+E=?","a":"8"}]', '[{"q":"12×3=?","a":"36"}]', '[{"q":"Synonym of happy?","a":"joyful"}]', '[{"q":"Which is different: cube, square, sphere, rectangle","a":"sphere"}]', 'Solve step by step.', 8),
('Aptitude - Class 5', 5, 'Medium', '[{"q":"Complete pattern: 2,4,6,8,?","a":"10"}]', '[{"q":"50% of 40=?","a":"20"}]', '[{"q":"Choose correct spelling: recieve/receive","a":"receive"}]', '[{"q":"Folded cube shows which face?","a":"B"}]', 'Answer carefully.', 10),
('Aptitude - Class 6', 6, 'Medium', '[{"q":"If all roses are flowers, some flowers red, then some roses might be ___","a":"red"}]', '[{"q":"7×8=?","a":"56"}]', '[{"q":"Antonym of ancient?","a":"modern"}]', '[{"q":"Visualize 3D shape","a":"pyramid"}]', 'Use logic and observation.', 12),
('Aptitude - Class 7', 7, 'Hard', '[{"q":"If no fruits are cars, apples are fruits, then apples are not ___","a":"cars"}]', '[{"q":"3/4 of 80=?","a":"60"}]', '[{"q":"Synonym of bright?","a":"brilliant"}]', '[{"q":"Count faces of cube","a":"6"}]', 'Think critically.', 14),
('Aptitude - Class 8', 8, 'Hard', '[{"q":"If A>B and B>C then?","a":"A>C"}]', '[{"q":"Square root of 144=?","a":"12"}]', '[{"q":"Antonym of polite?","a":"rude"}]', '[{"q":"Visual rotation of square","a":"same"}]', 'Apply reasoning.', 15),
('Aptitude - Class 9', 9, 'Hard', '[{"q":"Odd one: apple, orange, carrot, banana","a":"carrot"}]', '[{"q":"12²=?","a":"144"}]', '[{"q":"Choose synonym: rapid","a":"fast"}]', '[{"q":"Which net forms cube?","a":"B"}]', 'Choose logically.', 15),
('Aptitude - Class 10', 10, 'Hard', '[{"q":"If no engineers are doctors, some doctors teachers, then?","a":"Cannot determine"}]', '[{"q":"(15×4)+20=?","a":"80"}]', '[{"q":"Antonym of complex?","a":"simple"}]', '[{"q":"Visualize 2D projection","a":"rectangle"}]', 'Reason through problems.', 18),
('Aptitude - Class 11', 11, 'Hard', '[{"q":"If p→q, q→r, then p→?","a":"r"}]', '[{"q":"log10(100)=?","a":"2"}]', '[{"q":"Synonym of obscure?","a":"unclear"}]', '[{"q":"3D symmetry","a":"mirror"}]', 'Answer analytically.', 20),
('Aptitude - Class 12', 12, 'Hard', '[{"q":"All A are B. Some B are C. Can we say some A are C?","a":"not certain"}]', '[{"q":"If x+y=10, xy=21, find x²+y²","a":"58"}]', '[{"q":"Meaning of ephemeral?","a":"short-lived"}]', '[{"q":"Rotate object in 3D","a":"same"}]', 'Solve critically.', 22);

CREATE TABLE IF NOT EXISTS typing_tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    task_name VARCHAR(255) NOT NULL,
    class_level INT NOT NULL CHECK (class_level BETWEEN 1 AND 12),
    difficulty_level ENUM('Easy', 'Medium', 'Hard') NOT NULL,
    prompt TEXT NOT NULL,
    instructions TEXT,
    word_limit_min INT DEFAULT 50,
    word_limit_max INT DEFAULT 200,
    estimated_time INT DEFAULT 10,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO typing_tasks
(task_name,class_level,difficulty_level,prompt,instructions,word_limit_min,word_limit_max,estimated_time)
VALUES
('Type Simple Words',1,'Easy','I like my school and my friends.','Type exactly as shown.',10,30,5),
('Short Sentences',2,'Easy','The sun rises in the east every morning.','Copy text carefully.',10,30,5),
('Daily Routine',3,'Medium','Write what you do after waking up.','Compose short passage.',20,50,7),
('Favorite Toy',4,'Medium','Describe your favorite toy and why.','Focus on grammar.',20,50,8),
('Weekend Story',5,'Medium','Write about your last weekend.','Use sentences properly.',30,80,9),
('My Hobby',6,'Medium','Describe your favorite hobby.','Be creative.',30,100,9),
('Technology Today',7,'Hard','How technology helps in studies.','Avoid mistakes.',40,120,10),
('Healthy Living',8,'Hard','Importance of exercise and good food.','Keep grammar correct.',50,120,10),
('Career Goals',9,'Hard','Essay about your dream career.','Plan structure.',60,150,12),
('Online Learning',10,'Hard','Advantages and challenges of online education.','Stay focused.',70,160,12),
('Social Media Impact',11,'Hard','How social media affects youth.','Use balanced points.',80,180,12),
('Future of AI',12,'Hard','How AI will change our world.','Type fluently.',100,200,15);

CREATE TABLE IF NOT EXISTS mathematical_comprehension_tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    task_name VARCHAR(255) NOT NULL,
    class_level INT NOT NULL CHECK (class_level BETWEEN 1 AND 12),
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

INSERT INTO mathematical_comprehension_tasks
(task_name, class_level, difficulty_level, problem_text, question1, question2, question3, answer1_options, answer2_options, answer3_type, instructions, estimated_time)
VALUES
('Counting Basics', 1, 'Easy',
 'Tom has 3 apples and 2 oranges. He gets 1 more apple from his friend.',
 'How many apples does Tom have now?',
 'How many fruits does Tom have in total?',
 'If Tom shares equally with a friend, how many each?',
 '["3","4","5","6"]',
 '["5","6","7","8"]',
 'number',
 'Read carefully and solve using simple counting.', 5),

('Simple Addition', 2, 'Easy',
 'Lily has 5 pencils and buys 3 more pencils.',
 'How many pencils does Lily have now?',
 'If she gives 2 pencils to her friend, how many remain?',
 'Solve the total number of pencils.',
 '["8","7","6","9"]',
 '["6","5","7","8"]',
 'number',
 'Use addition and subtraction to solve the questions.', 5),

('Basic Subtraction', 3, 'Easy',
 'John has 10 candies. He eats 4 candies.',
 'How many candies are left?',
 'If he finds 3 more candies, how many now?',
 'Calculate the total candies after finding more.',
 '["6","5","7","8"]',
 '["9","8","10","11"]',
 'number',
 'Perform subtraction and addition carefully.', 5),

('Simple Multiplication', 4, 'Medium',
 'A box contains 4 rows of 3 chocolates each.',
 'How many chocolates in total?',
 'If 2 boxes are combined, how many chocolates altogether?',
 'Solve the multiplication problems.',
 '["12","10","9","15"]',
 '["24","20","18","22"]',
 'number',
 'Use multiplication to calculate totals.', 6),

('Division Basics', 5, 'Medium',
 'There are 20 candies divided equally among 4 children.',
 'How many candies does each child get?',
 'If 5 more candies are added, how many per child?',
 'Solve the division problems.',
 '["5","4","6","7"]',
 '["6","5","7","8"]',
 'number',
 'Apply division to distribute equally.', 6),

('Fractions Introduction', 6, 'Medium',
 'A pizza is cut into 8 slices. John eats 3 slices.',
 'What fraction of the pizza did John eat?',
 'How many slices remain?',
 'Solve the fraction and subtraction questions.',
 '["3/8","1/2","2/8","1/4"]',
 '["5","4","6","3"]',
 'number',
 'Read the problem and solve fractions step by step.', 7),

('Decimals Basics', 7, 'Medium',
 'A bottle contains 1.5 liters of juice. John drinks 0.4 liters.',
 'How much juice remains?',
 'If he drinks another 0.3 liters, how much is left?',
 'Solve the decimal subtraction problems.',
 '["1.1","1.0","1.2","1.3"]',
 '["0.8","0.7","0.9","1.0"]',
 'number',
 'Use decimal subtraction carefully to get answers.', 7),

('Percentage Problems', 8, 'Medium',
 'A shop has 200 candies. 25% are sold on Monday.',
 'How many candies were sold?',
 'How many remain?',
 'Calculate percentages correctly.',
 '["50","40","60","45"]',
 '["150","160","140","155"]',
 'number',
 'Use percentage calculations for solving.', 8),

('Simple Algebra', 9, 'Hard',
 'If x + 5 = 12, find x.',
 'What is x?',
 'What is x + 3?',
 'If x is doubled, what is 2x?',
 '["7","6","5","8"]',
 '["10","9","8","11"]',
 'number',
 'Solve the algebra equation step by step.', 9),

('Geometry Basics', 10, 'Hard',
 'A rectangle has length 8 and width 5.', 
 'Calculate area?', 
 'Calculate perimeter?', 
 'Length of rectangle?', 
 '["40","35","45","50"]', 
 '["26","25","28","30"]', 
 'number', 
 'Apply formulas for area and perimeter.', 12),

('Intermediate Algebra', 11, 'Hard',
 'Solve for y: 2y + 3 = 11.', 
 'Value of y?', 
 'Double y?', 
 'y minus 1?', 
 '["4","5","3","6"]', 
 '["8","10","6","12"]', 
 'number', 
 'Solve carefully using algebra.', 12),

('Advanced Problem Solving', 12, 'Hard',
 'A shop sells 12 pens for $24. How much for 18 pens?', 
 'Cost of 12 pens?', 
 'Cost of 18 pens?', 
 'Cost of 1 pen?', 
 '["24","20","30","22"]', 
 '["36","32","40","38"]', 
 'number', 
 'Use ratio and proportion to solve.', 15);


CREATE TABLE IF NOT EXISTS writing_tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    task_name VARCHAR(255) NOT NULL,
    class_level INT NOT NULL CHECK (class_level BETWEEN 1 AND 12),
    difficulty_level ENUM('Easy', 'Medium', 'Hard') NOT NULL,
    prompt TEXT NOT NULL,
    instructions TEXT,
    word_limit_min INT DEFAULT 20,
    word_limit_max INT DEFAULT 100,
    estimated_time INT DEFAULT 10,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO writing_tasks
(task_name,class_level,difficulty_level,prompt,instructions,word_limit_min,word_limit_max,estimated_time)
VALUES
('My Family',1,'Easy','Write about your family.','Use simple sentences.',20,50,5),
('My Best Friend',2,'Easy','Describe your best friend.','Write neatly.',20,60,5),
('A Fun Day',3,'Medium','Narrate a fun day at school.','Use past tense.',30,80,6),
('My Pet',4,'Medium','Write about your pet.','Add feelings.',40,100,7),
('The Rainy Day',5,'Medium','Describe a rainy day.','Be descriptive.',50,100,8),
('My Ambition',6,'Medium','Write what you want to be.','Stay focused.',50,120,8),
('Importance of Books',7,'Hard','Explain why books are important.','Organize paragraphs.',70,150,9),
('Save Environment',8,'Hard','Write how to protect environment.','Give examples.',80,160,10),
('Discipline in Life',9,'Hard','Discuss importance of discipline.','Use formal tone.',90,180,10),
('Digital Learning',10,'Hard','Benefits of digital education.','Be analytical.',100,180,12),
('Women Empowerment',11,'Hard','Role of women in society.','Be thoughtful.',120,200,12),
('Future World',12,'Hard','Imagine life100years from now.','Be imaginative.',150,250,15);

CREATE TABLE IF NOT EXISTS user_task_attempts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    task_id INT NOT NULL,
    attempt_number INT NOT NULL,
    status ENUM('In Progress', 'Completed', 'Abandoned') DEFAULT 'In Progress',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    UNIQUE KEY unique_attempt (user_id, task_id, attempt_number)
);

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

SELECT id, name, class FROM users 
WHERE name IN ('Testing Parent 11', 'Testing Child 111', 'Testing Child 112', 'Testing Parent 2');
UPDATE users SET class = 'Class 6' WHERE id = 18;
UPDATE users SET class = 'Class 6' WHERE id = 19;
UPDATE users SET class = 'Class 7' WHERE id = 21;
UPDATE users SET class = 'Class 5' WHERE id = 22;

-- Create a table to track class history
CREATE TABLE class_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    school_id INT NOT NULL,
    class VARCHAR(50) NOT NULL,
    academic_year INT NOT NULL,
    total_students INT DEFAULT 0,
    total_parents INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (school_id) REFERENCES schools(id),
    UNIQUE KEY unique_class_year (school_id, class, academic_year)
);

-- Classes and Sections layer
CREATE TABLE IF NOT EXISTS school_classes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    school_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    academic_year INT DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (school_id) REFERENCES schools(id) ON DELETE CASCADE,
    UNIQUE KEY unique_school_class_year (school_id, name, academic_year)
);

CREATE TABLE IF NOT EXISTS class_sections (
    id INT AUTO_INCREMENT PRIMARY KEY,
    class_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (class_id) REFERENCES school_classes(id) ON DELETE CASCADE,
    UNIQUE KEY unique_class_section (class_id, name)
);

-- Map section to assigned assessments (by task_name from tasks table)
CREATE TABLE IF NOT EXISTS section_assessments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    section_id INT NOT NULL,
    task_name VARCHAR(100) NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (section_id) REFERENCES class_sections(id) ON DELETE CASCADE,
    FOREIGN KEY (task_name) REFERENCES tasks(task_name) ON DELETE CASCADE,
    UNIQUE KEY unique_section_task (section_id, task_name)
);