-- Create reading_comprehension_tasks table for age-based reading comprehension tasks
USE dyslexia_study;

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
