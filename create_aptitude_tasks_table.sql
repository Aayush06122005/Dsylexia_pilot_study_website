-- Create aptitude_tasks table for storing aptitude test tasks by age groups
USE dyslexia_study;

CREATE TABLE IF NOT EXISTS aptitude_tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    task_name VARCHAR(255) NOT NULL,
    age_min INT NOT NULL,
    age_max INT NOT NULL,
    difficulty_level ENUM('Easy', 'Medium', 'Hard') DEFAULT 'Medium',
         instructions TEXT,
     estimated_time VARCHAR(50),
     example TEXT,
    
    -- Logical Reasoning Section
    logical_question1 TEXT,
    logical_question1_options JSON,
    logical_question2 TEXT,
    logical_question2_options JSON,
    
    -- Numerical Ability Section
    numerical_question1 TEXT,
    numerical_question1_options JSON,
    numerical_question2 TEXT,
    numerical_question2_options JSON,
    
    -- Verbal Ability Section
    verbal_question1 TEXT,
    verbal_question1_options JSON,
    verbal_question2 TEXT,
    verbal_question2_options JSON,
    
    -- Spatial Reasoning Section
    spatial_question1 TEXT,
    spatial_question1_options JSON,
    spatial_question2 TEXT,
    spatial_question2_options JSON,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Insert sample aptitude tasks for different age groups
INSERT INTO aptitude_tasks (task_name, age_min, age_max, difficulty_level, instructions, estimated_time, example,
    logical_question1, logical_question1_options, logical_question2, logical_question2_options,
    numerical_question1, numerical_question1_options, numerical_question2, numerical_question2_options,
    verbal_question1, verbal_question1_options, verbal_question2, verbal_question2_options,
    spatial_question1, spatial_question1_options, spatial_question2, spatial_question2_options) 
VALUES 
    ('Aptitude Test - Ages 7-9', 7, 9, 'Easy', 'Complete all four sections of the aptitude test. Each section contains multiple-choice questions.', '30-45 minutes', 'Sample question: What comes next in the sequence 2, 4, 6, 8, ?',
        'Which number comes next in the sequence: 2, 4, 6, 8, ?', '["10", "9", "11", "12"]',
        'If all cats are animals and some animals are pets, then:', '["All cats are pets", "Some cats are pets", "No cats are pets", "Cannot determine"]',
        'What is 5 + 3?', '["6", "7", "8", "9"]',
        'If you have 4 apples and eat 2, how many are left?', '["1", "2", "3", "4"]',
        'Choose the word that best completes: Cat is to kitten as dog is to:', '["puppy", "baby", "young", "small"]',
        'Which word means the opposite of "big"?', '["small", "large", "huge", "tall"]',
        'If you fold a piece of paper in half, how many layers will you have?', '["1", "2", "3", "4"]',
        'Which shape has 3 sides?', '["circle", "square", "triangle", "rectangle"]'
    ),
    ('Aptitude Test - Ages 10-12', 10, 12, 'Medium', 'Complete all four sections of the aptitude test. Each section contains multiple-choice questions.', '45-60 minutes', 'Sample question: What comes next in the sequence 2, 6, 12, 20, ?',
        'Which number comes next in the sequence: 2, 6, 12, 20, ?', '["30", "28", "32", "34"]',
        'If all roses are flowers and some flowers are red, then:', '["All roses are red", "Some roses are red", "No roses are red", "Cannot determine"]',
        'What is 25% of 80?', '["15", "20", "25", "30"]',
        'If a train travels 120 km in 2 hours, what is its speed in km/h?', '["40", "50", "60", "70"]',
        'Choose the word that best completes the analogy: Book is to Reading as Fork is to:', '["eating", "cooking", "cutting", "washing"]',
        'Which word is a synonym for "Eloquent"?', '["silent", "articulate", "quiet", "shy"]',
        'If you fold a piece of paper in half twice, how many layers will you have?', '["2", "3", "4", "6"]',
        'Which shape would you get if you rotate a square 90 degrees clockwise?', '["same square", "rectangle", "diamond", "triangle"]'
    ),
    ('Aptitude Test - Ages 13-15', 13, 15, 'Hard', 'Complete all four sections of the aptitude test. Each section contains multiple-choice questions.', '60-75 minutes', 'Sample question: What comes next in the sequence 1, 3, 6, 10, 15, ?',
        'Which number comes next in the sequence: 1, 3, 6, 10, 15, ?', '["20", "21", "22", "23"]',
        'If all scientists are researchers and some researchers are professors, then:', '["All scientists are professors", "Some scientists are professors", "No scientists are professors", "Cannot determine"]',
        'What is 15% of 200?', '["25", "30", "35", "40"]',
        'If a car travels 300 km in 4 hours, what is its average speed?', '["60", "65", "70", "75"]',
        'Choose the word that best completes: Democracy is to Freedom as Dictatorship is to:', '["control", "power", "authority", "oppression"]',
        'Which word is an antonym for "Benevolent"?', '["kind", "generous", "malevolent", "charitable"]',
        'If you have a cube and paint all its faces, how many faces will be painted?', '["4", "5", "6", "8"]',
        'Which 3D shape has 8 vertices and 12 edges?', '["cube", "sphere", "cylinder", "cone"]'
    );
