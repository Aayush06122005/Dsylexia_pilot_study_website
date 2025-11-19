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
select * from schools;


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
select * from users;

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

-- CREATE TABLE IF NOT EXISTS audio_recordings (
--     id INT AUTO_INCREMENT PRIMARY KEY,
--     attempt_id INT NOT NULL,
--     filename VARCHAR(255) NOT NULL,
--     uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     FOREIGN KEY (attempt_id) REFERENCES user_task_attempts(id) ON DELETE CASCADE
-- );

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
ALTER TABLE comprehension_progress ADD COLUMN score INT DEFAULT 0, ADD COLUMN max_score INT DEFAULT 2;

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
    answers JSON NULL,
    current_section VARCHAR(50) NULL,
    answered_count INT DEFAULT 0,
    progress_percent INT DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (attempt_id) REFERENCES user_task_attempts(id) ON DELETE CASCADE
);
ALTER TABLE aptitude_progress ADD COLUMN max_score INT DEFAULT 4;
-- Update existing records to have proper max_score values
UPDATE comprehension_progress SET max_score = 2 WHERE max_score = 0;
UPDATE mathematical_comprehension_progress SET max_score = 3 WHERE max_score = 0;
UPDATE aptitude_progress SET max_score = 4 WHERE max_score = 0;

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
ALTER TABLE mathematical_comprehension_progress ADD COLUMN score INT DEFAULT 0, ADD COLUMN max_score INT DEFAULT 3;

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
('Reading Task - Class 1', 1, 'Easy', 'The cat runs. I see the sun. The car is red.', 'Please read these sentences aloud.', 3),
('Reading Task - Class 2', 2, 'Easy', 'A little frog sat on a log. He was green with brown spots. He liked to eat bugs.', 'Please read this short paragraph aloud.', 3),
('Reading Task - Class 3', 3, 'Medium', 'You have a few crayons, Red, yellow and blue. Green, purple and black, I have some too. I need the red and you need the black. If we share our crayons, we have a full pack!', 'Please read this story aloud.', 4),
('Reading Task - Class 4', 4, 'Medium', 'Together we stand, strong and tall, Helping each other, we never fall. Cheering aloud, we shout and sing, Teamwork can overcome anything. Win or lose, we always share, Our bond of trust is always there.', 'Please read this poem aloud.', 4),
('Reading Task - Class 5', 5, 'Medium', 'It was a summer afternoon. Gopi was sitting in the veranda, reading a book. Suddenly, he heard something rustling past and falling with a thud in the garden. He wondered what it could be. Perhaps, it was a mango falling from the tree. Immediately, Gopi put his book aside, got up, and ran into the garden.', 'Please read this story aloud.', 4),
('Reading Task - Class 6', 6, 'Medium', 'Gajaraj, the elephant, lived in the best booth of the royal stables. The king was fond of Gajaraj, and he had ordered that the elephant should be well looked after. In spite of royal comforts, Gajaraj was sad because he had no friends. The mahout, or elephant trainer, was the only one he ever interacted with.', 'Please read this story aloud.', 4),
('Reading Task - Class 7', 7, 'Hard', 'There are many ancient places to visit in India. For example, Rani-ki-Vav (the Queen’s Stepwell) is located at Patan, Gujarat and is also on the World Heritage list by UNESCO. Stepwells are a distinctive form of water resource and storage systems on the Indian subcontinent, and were constructed during ancient times. They evolved over time from what was basically a pit in sandy soil towards elaborate multi-storey works of art and architecture.', 'Please read the passage out loud.', 5),
('Reading Task - Class 8', 8, 'Hard', 'The Vijayanagara Empire was renowned for its glory, wealth, and cultural achievements. Among its many illustrious rulers, King Krishnadeva Raya (ruled 1509–29 CE) stood out as a wise and powerful monarch. His reign is often referred to as the Golden Era of the Vijayanagara Empire, a time when art, literature, and architecture flourished. A great patron of learning, Krishnadeva Raya was not only an eminent warrior but also a gifted poet.', 'Please read the passage out loud.', 5),
('Reading Task - Class 9', 9, 'Hard', 'Rush hour crowds jostle for position on the underground train platform. A slight girl, looking younger than her seventeen years, was nervous yet excited as she felt the vibrations of the approaching train. It was her first day at the prestigious Royal Academy of Music in London and daunting enough for any teenager fresh from a Scottish farm. But this aspiring musician faced a bigger challenge than most: she was profoundly deaf.', 'Please read the passage out loud.', 5),
('Reading Task - Class 10', 10, 'Hard', 'Our elders are often heard reminiscing nostalgically about those good old Portuguese days, the Portuguese and their famous loaves of bread. Those eaters of loaves might have vanished but the makers are still there. We still have amongst us the mixers, the moulders and those who bake the loaves. Those age-old, time-tested furnaces still exist. The fire in the furnaces has not yet been extinguished.', 'Please read the passage out loud.', 5),
('Reading Task - Class 11', 11, 'Hard', 'One day back there in the good old days when I was nine and the world was full of every imaginable kind of magnificence, and life was still a delightful and mysterious dream, my cousin Mourad, who was considered crazy by everybody who knew him except me, came to my house at four in the morning and woke me up tapping on the window of my room. Aram, he said. I jumped out of bed and looked out of the window. My cousin Mourad was sitting on a beautiful white horse.', 'Please read the passage out loud.', 6),
('Reading Task - Class 12', 12, 'Hard', 'The presidents of the New York Central and the New York, New Haven and Hartford railroads will swear on a stack of timetables that there are only two. But I say there are three, because I’ve been on the third level of the Grand Central Station. Yes, I’ve taken the obvious step: I talked to a psychiatrist friend of mine, among others. I told him about the third level at Grand Central Station, and he said it was a waking-dream wish fulfillment.', 'Please read the passage out loud.', 6);

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
    answer1 TEXT, answer2 TEXT,
    instructions TEXT,
    estimated_time INT DEFAULT 5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO reading_comprehension_tasks 
(task_name, class_level, difficulty_level, passage, question1, question2, question3, 
 answer1_options, answer2_options, answer3_type, answer1, answer2, instructions, estimated_time) 
VALUES
('Comprehension - The Cat and the Mat', 1, 'Easy', 
 'The cat sat on the mat. It saw a bird. It ran around.', 
 'Who sat on the mat?', 
 'What animal is in the story?', 
 'Where was the cat?', 
 '["cat","dog","bird","fish"]', 
 '["tree","cat","chair","car"]', 
 'text', 
 'cat', 
 'cat', 
 'Please answer the following questions based on the passage given.', 
 5),

('Comprehension - The Red Kite', 2, 'Easy', 
 'A girl has a red kite. She flies it in the park.', 
 'What color is the kite?', 
 'Where does he fly it?', 
 'Who has the kite?', 
 '["red","blue","green","yellow"]', 
 '["school","home","park","beach"]', 
 'text', 
 'red', 
 'park', 
 'Please answer the following questions based on the passage given.', 
 5),

('Comprehension - Leo the Lion', 3, 'Medium', 
 'Leo the lion was not like the others. While his friends practiced their loud roars, Leo loved to quietly watch the clouds. One day, a big storm came. All the lions were scared of the thunder, but Leo was calm because he understood the clouds.', 
 'What did Leo love to do?', 
 'Why were the other lions scared?', 
 'Why was Leo calm during the storm?', 
 '["roar loudly","watch the clouds","chase mice","sleep all day"]', 
 '["of the dark","of the rain","of the thunder","of Leo"]', 
 'text', 
 'watch the clouds', 
 'of the thunder', 
 'Please answer the following questions based on the passage given.', 
 5),

('Comprehension - The Water Cycle', 4, 'Medium', 
 'The water cycle is how water moves around our planet. First, the sun heats up water in rivers and oceans, and it turns into vapor. This is called evaporation. The vapor rises, gets cold, and forms clouds. When the clouds get heavy, the water falls back to Earth as rain.', 
 'What is the first step of the water cycle mentioned in the passage?', 
 'What does the water vapor form when it gets cold?', 
 'What happens when the clouds get too heavy?', 
 '["condensation","precipitation","evaporation","collection"]', 
 '["rain","sun","ice","clouds"]', 
 'text', 
 'evaporation', 
 'clouds', 
 'Please answer the following questions based on the passage given.', 
 5),

('Comprehension - Marie Curie', 5, 'Medium', 
 'Marie Curie was a pioneering scientist born in Poland in 1867. She was fascinated by rays given off by an element called uranium. Her groundbreaking research led to the discovery of two new elements, polonium and radium. For her work, she became the first woman to win a Nobel Prize and the only person to win it in two different scientific fields.', 
 'What element first fascinated Marie Curie?', 
 'Marie Curie was the first woman to do what?', 
 'In which country was Marie Curie born?', 
 '["polonium","oxygen","radium","uranium"]', 
 '["discover an element","go to university","win a Nobel Prize","become a doctor"]', 
 'text', 
 'uranium', 
 'win a Nobel Prize', 
 'Please answer the following questions based on the passage given.', 
 5),

('Comprehension - Photosynthesis', 6, 'Medium', 
 'Photosynthesis is the vital process through which green plants use sunlight to create their own food. The plant\'s leaves contain a green pigment called chlorophyll, which absorbs energy from the sun. This energy is used to convert carbon dioxide from the air and water from the soil into a sugar called glucose, which is the plant\'s food. As a byproduct, this process releases the oxygen we breathe.', 
 'What is the main purpose of photosynthesis?', 
 'The pigment that absorbs sunlight is called ______.', 
 'Besides food (glucose), what important gas does photosynthesis release into the air?', 
 '["to release oxygen","for plants to create food","to absorb water","to look green"]', 
 '["glucose","oxygen","carbon dioxide","chlorophyll"]', 
 'text', 
 'for plants to create food', 
 'chlorophyll', 
 'Please answer the following questions based on the passage given.', 
 5),

('Comprehension - Liam the Painter', 7, 'Hard', 
 'Liam stared at the blank canvas, his heart a mix of excitement and apprehension. For weeks, he had imagined this painting—a stormy sea crashing against defiant cliffs. He picked up his brush, but his hand hesitated. What if he couldn\'t capture the raw power he envisioned? "Just one stroke," he whispered to himself, a small act of courage. He dipped the brush in a deep, stormy blue.', 
 'Which word best describes Liam\'s feelings as he begins to paint?', 
 'What subject did Liam intend to paint?', 
 'What does the phrase "his hand hesitated" suggest about Liam\'s state of mind?', 
 '["angry","indifferent","anxious","overjoyed"]', 
 '["a calm forest","a bustling city","a stormy sea","a quiet portrait"]', 
 'text', 
 'anxious', 
 'a stormy sea', 
 'Please answer the following questions based on the passage given.', 
 5),

('Comprehension - The Silk Road', 8, 'Hard', 
 'The Silk Road was not a single road but an extensive network of trade routes connecting the East and West for over 1,500 years. It was instrumental in the exchange of goods like silk, spices, and precious metals. However, its significance extended beyond commerce; it was also a crucial conduit for the transmission of ideas, technologies, religions, and philosophies between different cultures, fundamentally shaping the course of world history.', 
 'What was the primary function of the Silk Road?', 
 'The passage suggests the Silk Road\'s most important legacy was ______.', 
 'Besides physical goods, name two other things that were exchanged along the Silk Road.', 
 '["military conquest","exploration","cultural and commercial exchange","tourism"]', 
 '["the amount of silk traded","its long-lasting physical roads","its role in spreading ideas and culture","the wealth it created for traders"]', 
 'text', 
 'cultural and commercial exchange', 
 'its role in spreading ideas and culture', 
 'Please answer the following questions based on the passage given.', 
 5),

('Comprehension - The Dormant Seed Speech', 9, 'Hard', 
 'In his famous speech, the leader proclaimed, "A dream deferred is not a dream denied. It is a seed, dormant through the winter of oppression, waiting for the spring of opportunity to burst forth." This metaphor served to galvanize his followers, transforming their feelings of impatience into a powerful sense of hope and inevitable triumph. He urged them to be the sun and rain that would nurture this seed.', 
 'What is the central metaphor used in the passage?', 
 'According to the speaker, what is the "winter of oppression"?', 
 'What effect was the leader\'s metaphor intended to have on his audience?', 
 '["a journey","a battle","a dormant seed","a dark night"]', 
 '["a season of cold weather","a time of hardship and injustice","a period of rest","a feeling of denial"]', 
 'text', 
 'a dormant seed', 
 'a time of hardship and injustice', 
 'Please answer the following questions based on the passage given.', 
 5),

('Comprehension - Automation and AI', 10, 'Hard', 
 'The rise of automation and artificial intelligence presents a complex duality in the modern economy. On one hand, it promises unprecedented efficiency, productivity gains, and the potential to solve intractable problems. On the other hand, it fuels legitimate concerns about widespread job displacement and the exacerbation of economic inequality. Navigating this transition requires a proactive, rather than reactive, approach, focusing on robust education systems, lifelong learning initiatives, and social safety nets to mitigate the disruptive consequences.', 
 'What is the main purpose of this passage?', 
 'The author advocates for a "proactive" approach. What does this imply?', 
 'According to the text, what is one major negative concern associated with automation?', 
 '["to argue against automation","to analyze the multifaceted impact of automation","to explain how artificial intelligence works","to praise technological advancement"]', 
 '["waiting for problems to arise before acting","acting in advance to prepare for challenges","halting all technological progress","ignoring the negative consequences"]', 
 'text', 
 'to analyze the multifaceted impact of automation', 
 'acting in advance to prepare for challenges', 
 'Please answer the following questions based on the passage given.', 
 5),

('Comprehension - Existentialism', 11, 'Hard', 
 'Existentialism, a philosophical movement prominent in the 20th century, posits that individuals are free and therefore responsible for their own development through acts of the will. At its core is the tenet "existence precedes essence," which means that a person first exists, thrown into the world without a predefined purpose, and only then defines their identity or "essence" through their choices and actions. Consequently, the existentialist view emphasizes the anxiety and absurdity of this radical freedom, yet also the profound opportunity to create one\'s own meaning in a meaningless universe.', 
 'The phrase "existence precedes essence" most nearly means:', 
 'What is the inherent emotional conflict described in existentialism?', 
 'What, according to existentialist philosophy, is the primary mechanism through which individuals define themselves?', 
 '["our actions are predetermined by our character","our identity is defined by us after we are born","our purpose in life is given to us at birth","our existence is essentially meaningless"]', 
 '["the conflict between logic and emotion","the struggle between good and evil","the tension between societal expectation and personal desire","the anxiety of total freedom versus the opportunity to create meaning"]', 
 'text', 
 'our identity is defined by us after we are born', 
 'the anxiety of total freedom versus the opportunity to create meaning', 
 'Please answer the following questions based on the passage given.', 
 5),

('Comprehension - Heisenberg Uncertainty Principle', 12, 'Hard', 
 'The Heisenberg Uncertainty Principle is a foundational concept in quantum mechanics, articulating a fundamental limit to the precision with which certain pairs of physical properties of a particle, known as complementary variables (such as position and momentum), can be known simultaneously. The principle is not a statement about the limitations of our measurement technology, but rather an inherent property of quantum systems themselves. The more precisely the position of a particle is determined, the less precisely its momentum can be known, and vice versa. This probabilistic, rather than deterministic, nature of the quantum world represents a radical departure from the classical mechanics of Newton.', 
 'What is the central idea of the Heisenberg Uncertainty Principle?', 
 'The passage explicitly states that the principle is due to:', 
 'How does the quantum worldview described here contrast with that of classical mechanics?', 
 '["our measurement tools are not yet advanced enough","particles do not have a definite position or momentum","there is a fundamental trade-off in the precision of measuring complementary properties","quantum mechanics is less accurate than classical mechanics"]', 
 '["errors in the measurement process","the inherent nature of quantum systems","the large size of subatomic particles","a flaw in quantum theory"]', 
 'text', 
 'there is a fundamental trade-off in the precision of measuring complementary properties', 
 'the inherent nature of quantum systems', 
 'Please answer the following questions based on the passage given.', 
 5);

-- Create aptitude_tasks table for age-based aptitude tasks
CREATE TABLE IF NOT EXISTS aptitude_tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    task_name VARCHAR(255) NOT NULL,
    class_level INT NOT NULL CHECK (class_level BETWEEN 1 AND 12),
    difficulty_level ENUM('Easy', 'Medium', 'Hard') NOT NULL,
    
    -- Logical Reasoning
    logical_question TEXT,
    logical_question_options JSON,
    logical_answer TEXT,
    
    -- Numerical Ability
    numerical_question TEXT,
    numerical_question_options JSON,
    numerical_answer TEXT,
    
    -- Verbal Ability
    verbal_question TEXT,
    verbal_question_options JSON,
    verbal_answer TEXT,
    
    -- Spatial Reasoning
    spatial_question TEXT,
    spatial_question_options JSON,
    spatial_answer TEXT,
    
    instructions TEXT,
    estimated_time INT DEFAULT 15,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO aptitude_tasks (
    task_name, class_level, difficulty_level,
    logical_question, logical_question_options, logical_answer,
    numerical_question, numerical_question_options, numerical_answer,
    verbal_question, verbal_question_options, verbal_answer,
    spatial_question, spatial_question_options, spatial_answer,
    instructions, estimated_time
) VALUES
('Aptitude - Class 1', 1, 'Easy',
 'If sun is day, moon is ___', '["night", "day", "morning", "evening"]', 'night',
 '2+2=?', '["3", "4", "5", "6"]', '4',
 'Opposite of hot?', '["cold", "warm", "cool", "fire"]', 'cold',
 'Which shape has 3 sides?', '["triangle", "square", "circle", "rectangle"]', 'triangle',
 'Answer simple reasoning questions.', 4),

('Aptitude - Class 2', 2, 'Easy',
 'Which one does not belong? Apple, Banana, Car, Orange', '["Apple", "Banana", "Car", "Orange"]', 'Car',
 '8+7=?', '["14", "15", "16", "17"]', '15',
 'Rearrange the letters to make a word: T-A-C', '["CAT", "ACT", "TAC", "ATC"]', 'CAT',
 'How many corners does a square have?', '["3", "4", "5", "6"]', '4',
 'Think and choose the correct answer.', 4),

('Aptitude - Class 3', 3, 'Medium',
 'Which one does not belong? Pen, Crayon, Book, Pencil', '["Pen", "Crayon", "Book", "Pencil"]', 'Book',
 '6×4=?', '["20", "22", "23", "24"]', '24',
 'Rearrange the letters to make a word: R-A-W-T-E', '["WATER", "RETAW", "TAWER", "TARWE"]', 'WATER',
 'How many edges does a cube have?', '["8", "10", "12", "14"]', '12',
 'Solve basic logic and math problems.', 5),

('Aptitude - Class 4', 4, 'Medium',
 'Which one does not belong? Ice, Water, Rock, Steam', '["Ice", "Water", "Rock", "Steam"]', 'Rock',
 '21 ÷ 3 = ?', '["6", "7", "8", "9"]', '7',
 'Rearrange the letters to make a word: L-E-P-P-A', '["APPLE", "PEPAL", "LEAPP", "APPEL"]', 'APPLE',
 'Which of the following letters has a line of symmetry?', '["F", "J", "A", "G"]', 'A',
 'Solve step by step.', 6),

('Aptitude - Class 5', 5, 'Medium',
 'Which one does not belong? Happy, Sad, Run, Angry', '["Happy", "Sad", "Run", "Angry"]', 'Run',
 'What is 1/2 of 50?', '["20", "25", "30", "40"]', '25',
 'Rearrange the letters to make a word: C-S-E-I-N-E-C', '["SCIENCE", "SECINCE", "CENSICE", "SCINECE"]', 'SCIENCE',
 'Find the next shape in the pattern: ●, ▲, ■, ●, ▲, ?', '["■", "▲", "●", "◆"]', '■',
 'Answer carefully.', 7),

('Aptitude - Class 6', 6, 'Medium',
 'Which one does not belong? Sparrow, Eagle, Ostrich, Crow', '["Sparrow", "Eagle", "Ostrich", "Crow"]', 'Ostrich',
 '3.5 + 2.25 = ?', '["5.5", "5.6", "5.75", "6"]', '5.75',
 'Rearrange the letters to make a word: T-S-E-I-L-N', '["SILENT", "LISTEN", "TINELS", "LENTIS"]', 'SILENT',
 'How many squares are needed to make the net of a cube?', '["4", "5", "6", "8"]', '6',
 'Use logic and observation.', 8),

('Aptitude - Class 7', 7, 'Hard',
 'Which one does not belong? Triangle, Square, Sphere, Circle', '["Triangle", "Square", "Sphere", "Circle"]', 'Sphere',
 'What is 20% of 80?', '["10", "12", "16", "20"]', '16',
 'Rearrange the letters to make a word: D-R-A-G-N-E', '["GARDEN", "DANGER", "GRADEN", "DRANGE"]', 'GARDEN',
 'Which shape will look the same after a 90-degree rotation?', '["Square", "Rectangle", "Triangle", "Letter F"]', 'Square',
 'Think critically.', 10),

('Aptitude - Class 8', 8, 'Hard',
 'Which one does not belong? Addition, Subtraction, Equation, Multiplication', '["Addition", "Subtraction", "Equation", "Multiplication"]', 'Equation',
 'If 2x + 4 = 12, what is x?', '["2", "3", "4", "5"]', '4',
 'Rearrange the letters to make a word: G-L-E-K-D-O-W-N', '["KNOWLEDGE", "GLOWENKED", "KNEWLODGE", "WONKEDGLE"]', 'KNOWLEDGE',
 'What is the mirror image of the number 50?', '["05", "02", "20", "50"]', '02',
 'Apply reasoning.', 12),

('Aptitude - Class 9', 9, 'Hard',
 'Which one does not belong? Joyful, Cheerful, Gloomy, Ecstatic', '["Joyful", "Cheerful", "Gloomy", "Ecstatic"]', 'Gloomy',
 'The side of a square is 6 cm. What is its area?', '["30", "35", "36", "40"]', '36 cm²',
 'Rearrange the words: always truth the speak', '["Speak the truth always", "Always speak the truth", "Truth always the speak", "Always the speak truth"]', 'Always speak the truth',
 'If 1 is on top of a dice, what is at the bottom?', '["6", "5", "4", "3"]', '6',
 'Choose logically.', 13),

('Aptitude - Class 10', 10, 'Hard',
 'Find the odd one: 2, 4, 6, 8, 9, 10', '["8", "9", "10", "6"]', '9',
 'Probability of drawing a king from a deck?', '["1/52", "1/26", "1/13", "4/52"]', '1/13',
 'Complete the analogy: Doctor is to Stethoscope as Carpenter is to ___.', '["Saw", "Hammer", "Nails", "Wood"]', 'Saw',
 'How many triangles are in a Star of David?', '["6", "8", "10", "12"]', '8',
 'Reason through problems.', 15),

('Aptitude - Class 11', 11, 'Hard',
 'If all roses are flowers, and some flowers fade quickly, which conclusion is certain?', '["All roses fade quickly", "Some roses fade quickly", "No roses fade quickly", "No certain conclusion can be drawn"]', 'No certain conclusion can be drawn',
 'If sin(θ) = cos(θ), what is θ (0°–90°)?', '["30°", "45°", "60°", "90°"]', '45°',
 'Identify the error: The team are playing very well today.', '["are should be is", "team should be teams", "playing should be plays", "very should be too"]', 'are should be is',
 'A paper is folded twice and a hole is punched; how many holes when unfolded?', '["2", "3", "4", "6"]', '4',
 'Answer analytically.', 18),

('Aptitude - Class 12', 12, 'Hard',
 'A company’s profits rise for 5 years; CEO credits marketing. This assumes that?', '["profits will continue", "no other factor caused profit", "marketing is most important", "company wasn’t profitable before"]', 'no other factor caused profit',
 'Derivative of f(x)=3x²+5?', '["3x", "6x", "2x", "x²"]', '6x',
 'Meaning of “to beat around the bush”?', '["To avoid saying something directly", "To be aggressive", "To confuse", "To talk too much"]', 'To avoid saying something directly',
 'A cube is painted on all six faces and then cut into 64 smaller, equal-sized cubes.
How many of these smaller cubes will have exactly two faces painted?', '["8","12","24","48"]', '24',
 'Solve critically.', 20);

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
('My School and Friends',1,'Easy','I like my school and my friends.','Please type the sentences shown.',0,7,3),
('The Rising Sun',2,'Easy','The sun rises in the east every morning.','Please type the sentences shown.',0,8,3),
('Soil and Living Things',3,'Medium','Soil is the topmost layer of the Earth’s surface. Soil is made from rocks that have broken up into tiny pieces, as well as old leaves, roots, stems and living and dead animals like insects.','Please type the sentences shown.',0,35,4),
('Mystery Masala Stall',4,'Medium','Mukesh and his friends lined up at a colourful stall named ‘Mystery Masala’ to try a unique food made by their classmates. This food had a hint of sweetness, it was also a little salty, and a bit bitter too.','Please type the sentences shown.',0,38,4),
('Republic Day Parade',5,'Medium','We enjoyed watching the Republic Day parade in New Delhi, the fighter jets flying in the sky, the state tableaux and the cultural programmes! The parade also featured the Indian Defence Forces, the Army, the Navy, the Airforce, the paramilitary and other forces.','Please type the sentences shown.',0,44,4),
('Handpicking Method',6,'Medium','The method of picking by hand from a mixture (when two or more substances are mixed) such as small stones and husk from wheat and rice is called handpicking. It is done on the basis of differences in size, colour and shape of the particles.','Please type the sentences shown.',0,39,4),
('Managing School Tasks',7,'Hard','A school is full of activities and things that must be done. Many day-to-day tasks need to be managed, and things need to be organised. For example, there are timetables to be made and followed, sports activities to be organised, food to be served during lunch time (also called the mid-day-meal), utensils to be cleaned, speakers to be decided for the morning assembly, and activities to be arranged for ‘No Bag Days’.','Please type the sentences shown.',0,74,5),
('Picnic and Air Pressure',8,'Hard','Megha and her brother Pawan are going on a picnic. They walk to the picnic spot, carrying identical items in their bags. On the way, Pawan keeps adjusting his bag, and looks uncomfortable. Megha asks, “Is there a problem with your bag?” Pawan responds, “Yes, it is hurting my shoulders.” Megha says, “Both our bags are equally heavy. Why does your bag hurt, and mine doesn’t?”','Please type the sentences shown.',0,77,5),
('Climate of India',9,'Hard','The Tropic of Cancer passes through the middle of the country from the Rann of Kuchchh in the west to Mizoram in the east. Almost half of the country, lying south of the Tropic of Cancer, belongs to the tropical area. All the remaining area, north of the Tropic, lies in the sub-tropics. Therefore, India’s climate has characteristics of tropical as well as subtropical climates.','Please type the sentences shown.',0,65,5),
('Understanding Federalism',10,'Hard','Federalism is a system of government in which the power is divided between a central authority and various constituent units of the country. Usually, a federation has two levels of government. One is the government for the entire country that is usually responsible for a few subjects of common national interest. The others are governments at the level of provinces or states that look after much of the day-to-day administering of their state. Both these levels of governments enjoy their power independent of the other.','Please type the sentences shown.',0,95,5),
('E-Business and Technology',11,'Hard','Electronic mode of doing business, or e-business as it is referred to, presents the firm with promising opportunities for anything, anywhere and anytime to its customers, thereby, dismantling the time and space/locational constraints on its performance. Though e-business is high-tech, it suffers from the limitation of being low in personal touch. The customers as a result do not get attended to on an interpersonal basis. Besides, there are concerns over security of e-transactions and privacy of those who transact business over the internet.','Please type the sentences shown.',0,109,6),
('Rural Livelihoods in India',12,'Hard','Agriculture is the single most important source of livelihood for the majority of the rural population. But the rural is not just agriculture. Many activities that support agriculture and village life are also sources of livelihood for people in rural India. For example, a large number of artisans such as potters, carpenters, weavers, ironsmiths, and goldsmiths are found in rural areas. They were once part and parcel of the village economy. Their numbers have been steadily lessening since the colonial period.','Please type the sentences shown.',0,103,6);

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
    answer1 TEXT, answer2 TEXT , answer3 TEXT,
    instructions TEXT,
    estimated_time INT DEFAULT 5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO mathematical_comprehension_tasks
(task_name, class_level, difficulty_level, problem_text,
 question1, question2, question3,
 answer1_options, answer2_options, answer3_type,
 answer1, answer2, answer3, instructions, estimated_time)
VALUES
-- CLASS 1
('Crayon Counting', 1, 'Easy',
 'Ria has 4 red crayons and 2 blue crayons. Her teacher gives her 1 more red crayon.',
 'How many red crayons does Ria have now?',
 'How many crayons does Ria have in total?',
 'If Ria loses 1 blue crayon, how many blue crayons are left?',
 '["4","5","6","7"]',
 '["6","7","8","9"]',
 'number',
 '5', '8', '1',
 'Read carefully and use addition or subtraction to solve.', 6),

-- CLASS 2
('Farm Animal Count', 2, 'Easy',
 'A farmer has 10 chickens and 8 cows. He sells 3 of his chickens at the market.',
 'How many chickens does the farmer have left?',
 'How many animals does the farmer have in total now?',
 'If 2 new cows are born, how many cows will the farmer have?',
 '["5","6","7","8"]',
 '["15","16","17","18"]',
 'number',
 '7', '15', '10',
 'Count carefully using addition and subtraction.', 6),

-- CLASS 3
('Cookie Tray Math', 3, 'Easy',
 'A baker bakes 5 trays of cookies. Each tray has 6 cookies. He sells 10 cookies in the morning.',
 'How many cookies did the baker make in total?',
 'How many cookies are left after the morning sale?',
 'If he bakes one more tray of 6 cookies, how many cookies will he have now?',
 '["25","30","35","40"]',
 '["10","15","20","25"]',
 'number',
 '30', '20', '26',
 'Multiply and subtract carefully to find each answer.', 6),

-- CLASS 4
('Library Books', 4, 'Medium',
 'A library has 150 books. On Monday, 25 books were borrowed. On Tuesday, 10 of the borrowed books were returned.',
 'How many books were out of the library after Monday?',
 'How many books were in the library at the end of Tuesday?',
 'If 20 more books are borrowed on Wednesday, how many books will be out of the library in total?',
 '["125","135","150","175"]',
 '["115","125","135","145"]',
 'number',
 '125', '135', '35',
 'Track each day’s changes step by step.', 6),

-- CLASS 5
('Pizza Fractions', 5, 'Medium',
 'A pizza is cut into 8 equal slices. Aman eats 1/4 of the pizza, and Ben eats 1/2 of the pizza.',
 'How many slices did Aman eat?',
 'How many slices did Ben eat?',
 'How many slices are left?',
 '["1","2","3","4"]',
 '["2","3","4","5"]',
 'number',
 '2', '4', '2',
 'Use fraction understanding to solve slice problems.', 6),

-- CLASS 6
('Park Perimeter and Area', 6, 'Medium',
 'A rectangular park is 40 meters long and 20 meters wide. A path is built around its outer edge.',
 'What is the perimeter of the park?',
 'What is the area of the park?',
 'If a person jogs 3 complete laps around the park, what is the total distance they cover in meters?',
 '["60","80","100","120"]',
 '["600","800","1000","1200"]',
 'number',
 '120', '800', '360',
 'Apply perimeter and area formulas carefully.', 6),

-- CLASS 7
('Discount and Profit', 7, 'Medium',
 'A shop offers a 20% discount on a T-shirt that has a marked price of ₹500. The shopkeeper still makes a profit of ₹50 on the sale.',
 'What is the value of the discount?',
 'What is the selling price of the T-shirt after the discount?',
 'What was the original cost price of the T-shirt for the shopkeeper?',
 '["20","50","100","150"]',
 '["350","400","450","480"]',
 'number',
 '100', '400', '350',
 'Solve percentage and profit problems carefully.', 6),

-- CLASS 8
('Speed and Fuel', 8, 'Medium',
 'A car travels at a constant speed and covers a distance of 180 km in 3 hours. The car consumes 1 liter of fuel for every 15 km it travels.',
 'What is the speed of the car in km/h?',
 'How much fuel would the car consume to travel the 180 km distance?',
 'How many kilometers can the car travel with a full tank of 40 liters of fuel?',
 '["50","60","70","80"]',
 '["10","12","15","18"]',
 'number',
 '60', '12', '600',
 'Use speed = distance/time and ratio for fuel.', 6),

-- CLASS 9
('Triangle Prism', 9, 'Hard',
 'A right-angled triangle has a base of 8 cm and a height of 6 cm. This triangle is the base of a prism which has a length of 10 cm.',
 'What is the length of the hypotenuse of the triangle?',
 'What is the area of the triangular base?',
 'What is the volume of the prism in cm³?',
 '["9","10","12","14"]',
 '["24","30","40","48"]',
 'number',
 '10', '24', '240',
 'Apply Pythagoras theorem and volume formula.', 6),

-- CLASS 10
('Probability of Balls', 10, 'Hard',
 'A bag contains 5 red balls, 3 blue balls, and 2 green balls. One ball is drawn at random from the bag.',
 'What is the total number of possible outcomes?',
 'What is the probability of drawing a blue ball?',
 'If two red balls are removed from the bag, what is the new probability of drawing a red ball, expressed as a fraction a/b?',
 '["3","5","8","10"]',
 '["3/10","1/5","1/2","3/7"]',
 'number',
 '10', '3/10', '3/8',
 'Understand total outcomes and basic probability.', 6),

-- CLASS 11
('Particle Motion', 11, 'Hard',
 'The position of a particle moving along a straight line is given by s(t) = t^2 - 4t + 3, where t is time in seconds and s is position in meters.',
 'What is the initial position of the particle at t = 0?',
 'At what time t does the particle momentarily stop (velocity = 0)?',
 'What is the particle\'s position when it stops?',
 '["0","1","2","3"]',
 '["1","2","3","4"]',
 'number',
 '3', '2', '-1',
 'Use differentiation to find velocity and position.', 6),

-- CLASS 12
('Exponential Growth Model', 12, 'Hard',
 'The rate of growth of a bacterial colony is given by dP/dt = 2P, where P is the population and t is time in hours. The initial population at t=0 is 100.',
 'The population growth model is best described as:',
 'What is the rate of population growth at t=0?',
 'Given P(t) = 100e^{2t}, what is the approximate population after 1 hour? (Use e ≈ 2.72)',
 '["Linear","Quadratic","Exponential","Logarithmic"]',
 '["100 bacteria/hr","200 bacteria/hr","50 bacteria/hr","0 bacteria/hr"]',
 'number',
 'Exponential', '200 bacteria/hr', '739',
 'Understand exponential growth and apply the model.', 6);


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
(task_name, class_level, difficulty_level, prompt, instructions, word_limit_min, word_limit_max, estimated_time)
VALUES
-- CLASS 1
('Two Little Hands', 1, 'Easy',
'Two little hands go clap, clap, clap. Two little legs go tap, tap, tap.',
'Write a few lines imagining what else your hands and legs can do.', 0, 14, 10),

-- CLASS 2
('The Sun and the Wind', 2, 'Easy',
'The Sun and the Wind had a fight. "I am stronger than you," said the Wind. "No, you are not," said the Sun. A man was walking down the road. He was wearing a coat. The Sun said, "I have a plan. Let us see who can get his coat off."',
'Rewrite the story ending in your own words.', 0, 59, 10),

-- CLASS 3
('Save Water', 3, 'Medium',
'Water is very important for life. We get water from rain, rivers, ponds, and wells. All animals and plants need water to live. We use water for many things in our daily life, such as drinking, cooking, washing, and growing crops. We must not waste water.',
'Write about ways to save water in your daily life.', 0, 56, 10),

-- CLASS 4
('Reaching School', 4, 'Medium',
'In many parts of India, children face challenges to reach school. In Ladakh, children must cross wide, frozen rivers. In Kerala, some children use a small wooden boat called a vallam to reach their school. In the jungles of Assam, they often walk across strong bamboo bridges built over rivers.',
'Describe how you travel to school and the challenges you face.', 0, 63, 10),

-- CLASS 5
('Helen Keller', 5, 'Medium',
'Helen Keller was born in 1880. When she was a young child, she became blind and deaf. She could not see or hear. She was often angry. Then, a teacher named Anne Sullivan came to help her. Anne taught Helen how to spell words with her fingers. This changed her life completely.',
'Write about someone who inspires you and why.', 0, 60, 10),

-- CLASS 6
('Components of Food', 6, 'Medium',
'Our food consists of several components. The major nutrients are carbohydrates, proteins, fats, vitamins, and minerals. In addition, food also contains dietary fibre and water. Carbohydrates and fats mainly provide energy to our body. Proteins are needed for the growth and repair of our body.',
'Write about your favourite healthy meal and why it is good for health.', 0, 56, 10),

-- CLASS 7
('Our Environment', 7, 'Medium',
'The place, people, things, and nature that surround any living organism is called the environment. It is a combination of natural and human-made components. The natural environment includes the lithosphere, hydrosphere, atmosphere, and biosphere. The lithosphere is the solid crust or the hard top layer of the Earth.',
'Write about how humans can protect the environment.', 0, 59, 10),

-- CLASS 8
('East India Company', 8, 'Hard',
'The East India Company arrived in 1600, acquiring a charter from Queen Elizabeth I of England, granting it the sole right to trade with the East. Its primary interest was trade, not territory. However, conflicts over trade concessions and fortifications eventually led to political interference. The Battle of Plassey in 1757 marked the first major victory for the Company in India.',
'Write how trade led to British control in India.', 0, 72, 10),

-- CLASS 9
('Law of Conservation of Mass', 9, 'Hard',
'The law of conservation of mass states that mass can neither be created nor destroyed in a chemical reaction. This means that in any chemical reaction, the total mass of the reactants must be equal to the total mass of the products. For example, if 12 grams of carbon react completely with 32 grams of oxygen, exactly 44 grams of carbon dioxide will be formed.',
'Explain the law in your own words and give another example.', 0, 65, 10),

-- CLASS 10
('Three Sectors of Economy', 10, 'Hard',
'We can classify economic activities into three different sectors. The primary sector includes agriculture, forestry, and fishing, as it involves the direct use of natural resources. The secondary sector covers activities where natural products are changed into other forms through manufacturing; this is also called the industrial sector. The tertiary sector consists of activities that support the primary and secondary sectors, such as transportation, banking, and teaching.',
'Write about which sector you think is most important and why.', 0, 81, 12),

-- CLASS 11
('Measurement in Physics', 11, 'Hard',
'Measurement is the foundation of all experimental science and technology. To measure any physical quantity, we compare it with a basic, internationally accepted reference standard called a unit. The result of a measurement is expressed as a numerical value accompanied by the unit. The units for fundamental quantities like length, mass, and time are called fundamental units. For example, the SI unit for length is the metre (m) and for mass is the kilogram (kg).',
'Explain why standard units are important in science.', 0, 83, 15),

-- CLASS 12
('The Fall of the Berlin Wall', 12, 'Hard',
'The Berlin Wall, which had symbolised the division between the capitalist and the communist worlds, was felled by the people in November 1989. This event was followed by the disintegration of the Soviet Union itself, which formally ended the Cold War. The internal weaknesses of the Soviet economic and political system, combined with the reforms (perestroika and glasnost) introduced by Mikhail Gorbachev, led to this collapse. This marked the end of bipolarity in global politics.',
'Write about how the fall of the Berlin Wall changed world politics.', 0, 91, 15);

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

CREATE TABLE IF NOT EXISTS user_badge_notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    badge_name VARCHAR(255) NOT NULL,
    badge_icon VARCHAR(10) NOT NULL,
    badge_description TEXT NOT NULL,
    earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notified_at TIMESTAMP NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_badge_user (user_id, badge_name)
);

-- select * from user_badge_notifications;
-- SET FOREIGN_KEY_CHECKS = 0;
-- TRUNCATE TABLE section_assessments;
-- SET FOREIGN_KEY_CHECKS = 1;	
