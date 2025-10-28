-- Migration script to update aptitude_tasks table structure
-- This script adds individual question fields and migrates data from JSON format

-- First, create a backup of existing data
CREATE TABLE IF NOT EXISTS aptitude_tasks_backup AS SELECT * FROM aptitude_tasks;

-- Drop the old table
DROP TABLE IF EXISTS aptitude_tasks;

-- Create the new table structure
CREATE TABLE IF NOT EXISTS aptitude_tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    task_name VARCHAR(255) NOT NULL,
	class_level INT NOT NULL CHECK (class_level BETWEEN 1 AND 12),
    difficulty_level ENUM('Easy', 'Medium', 'Hard') NOT NULL,
    school_id INT NULL,
    
    -- Logical Reasoning Questions
    logical_question1 TEXT,
    logical_question1_options JSON,
    logical_question2 TEXT,
    logical_question2_options JSON,
    
    -- Numerical Ability Questions
    numerical_question1 TEXT,
    numerical_question1_options JSON,
    numerical_question2 TEXT,
    numerical_question2_options JSON,
    
    -- Verbal Ability Questions
    verbal_question1 TEXT,
    verbal_question1_options JSON,
    verbal_question2 TEXT,
    verbal_question2_options JSON,
    
    -- Spatial Reasoning Questions
    spatial_question1 TEXT,
    spatial_question1_options JSON,
    spatial_question2 TEXT,
    spatial_question2_options JSON,
    
    instructions TEXT,
    estimated_time INT DEFAULT 15,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Optional FK (safe even if schools table exists already)
ALTER TABLE aptitude_tasks 
    ADD CONSTRAINT fk_aptitude_tasks_school
    FOREIGN KEY (school_id) REFERENCES schools(id) ON DELETE SET NULL;

-- Insert the new data with single question per category
INSERT INTO aptitude_tasks (task_name, class_level, difficulty_level, logical_question, logical_question_options, numerical_question, numerical_question_options, verbal_question, verbal_question_options, spatial_question, spatial_question_options, instructions, estimated_time) VALUES
('Aptitude - Class 1', 1, 'Easy', 'If sun is day, moon is ___', '["night", "day", "morning", "evening"]', '2+2=?', '["3", "4", "5", "6"]', 'Opposite of hot?', '["cold", "warm", "cool", "fire"]', 'Which shape has 3 sides?', '["triangle", "square", "circle", "rectangle"]', 'Answer simple reasoning questions.', 5),

('Aptitude - Class 2', 2, 'Easy', 'If all cats are animals, Fluffy is a cat. Fluffy is?', '["animal", "plant", "car", "house"]', '3+5=?', '["6", "7", "8", "9"]', 'Synonym of big?', '["large", "small", "tiny", "huge"]', 'Square has how many corners?', '["3", "4", "5", "6"]', 'Think and choose the correct answer.', 6),

('Aptitude - Class 3', 3, 'Medium', 'Find odd one: cat, dog, fish, tree', '["tree", "cat", "dog", "fish"]', '10-6=?', '["3", "4", "5", "6"]', 'Opposite of fast?', '["slow", "quick", "rapid", "swift"]', 'Triangle has how many angles?', '["2", "3", "4", "5"]', 'Solve basic logic and math problems.', 7),

('Aptitude - Class 4', 4, 'Medium', 'If A=1, B=2, then C+E=?', '["8", "9", "10", "11"]', '12×3=?', '["35", "36", "37", "38"]', 'Synonym of happy?', '["joyful", "sad", "angry", "tired"]', 'Which is different: cube, square, sphere, rectangle?', '["sphere", "cube", "square", "rectangle"]', 'Solve step by step.', 8),

('Aptitude - Class 5', 5, 'Medium', 'Complete pattern: 2,4,6,8,?', '["10", "9", "11", "12"]', '50% of 40=?', '["15", "20", "25", "30"]', 'Choose correct spelling: recieve/receive', '["receive", "recieve", "recive", "receve"]', 'Folded cube shows which face?', '["B", "A", "C", "D"]', 'Answer carefully.', 10),

('Aptitude - Class 6', 6, 'Medium', 'If all roses are flowers, some flowers are red, then some roses might be ___', '["red", "blue", "green", "yellow"]', '7×8=?', '["54", "55", "56", "57"]', 'Antonym of ancient?', '["modern", "old", "aged", "vintage"]', 'Visualize 3D shape', '["pyramid", "square", "circle", "line"]', 'Use logic and observation.', 12),

('Aptitude - Class 7', 7, 'Hard', 'If no fruits are cars, apples are fruits, then apples are not ___', '["cars", "fruits", "food", "plants"]', '3/4 of 80=?', '["55", "60", "65", "70"]', 'Synonym of bright?', '["brilliant", "dark", "dim", "dull"]', 'Count faces of cube', '["4", "5", "6", "7"]', 'Think critically.', 14),

('Aptitude - Class 8', 8, 'Hard', 'If A>B and B>C then?', '["A>C", "A<C", "A=C", "Cannot determine"]', 'Square root of 144=?', '["10", "11", "12", "13"]', 'Antonym of polite?', '["rude", "nice", "kind", "good"]', 'Visual rotation of square', '["same", "different", "bigger", "smaller"]', 'Apply reasoning.', 15),

('Aptitude - Class 9', 9, 'Hard', 'Odd one: apple, orange, carrot, banana', '["carrot", "apple", "orange", "banana"]', '12²=?', '["140", "142", "144", "146"]', 'Choose synonym: rapid', '["fast", "slow", "steady", "calm"]', 'Which net forms cube?', '["B", "A", "C", "D"]', 'Choose logically.', 15),

('Aptitude - Class 10', 10, 'Hard', 'If no engineers are doctors, some doctors are teachers, then?', '["Cannot determine", "Some engineers are teachers", "No engineers are teachers", "All engineers are teachers"]', '(15×4)+20=?', '["75", "80", "85", "90"]', 'Antonym of complex?', '["simple", "hard", "difficult", "tough"]', 'Visualize 2D projection', '["rectangle", "circle", "triangle", "line"]', 'Reason through problems.', 18),

('Aptitude - Class 11', 11, 'Hard', 'If p→q, q→r, then p→?', '["r", "p", "q", "Cannot determine"]', 'log10(100)=?', '["1", "2", "3", "4"]', 'Synonym of obscure?', '["unclear", "clear", "bright", "obvious"]', '3D symmetry', '["mirror", "rotation", "translation", "scaling"]', 'Answer analytically.', 20),

('Aptitude - Class 12', 12, 'Hard', 'All A are B. Some B are C. Can we say some A are C?', '["not certain", "yes", "no", "always"]', 'If x+y=10, xy=21, find x²+y²', '["56", "58", "60", "62"]', 'Meaning of ephemeral?', '["short-lived", "permanent", "long", "eternal"]', 'Rotate object in 3D', '["same", "different", "bigger", "smaller"]', 'Solve critically.', 22);

-- Clean up backup table (optional - comment out if you want to keep backup)
-- DROP TABLE aptitude_tasks_backup;
