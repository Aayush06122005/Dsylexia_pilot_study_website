-- Create mathematical_comprehension_tasks table for age-based mathematical comprehension tasks
USE dyslexia_study;

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
