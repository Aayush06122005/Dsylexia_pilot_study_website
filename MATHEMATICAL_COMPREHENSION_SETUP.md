# Age-Based Mathematical Comprehension Tasks Setup Guide

## Overview
This implementation adds age-based mathematical comprehension tasks to the task4.html page. Users will see different mathematical word problems based on their age, making the experience personalized and appropriate for their mathematical understanding level.

## Database Setup

### 1. Create the mathematical_comprehension_tasks table
Run the SQL script `create_mathematical_comprehension_tasks_table.sql`:

```sql
-- Run this in your MySQL database
source create_mathematical_comprehension_tasks_table.sql;
```

This will create the table and insert sample tasks for different age groups:
- **Ages 6-8**: Simple Counting (Easy) - Basic counting and sharing problems
- **Ages 9-11**: Money Problems (Medium) - Money calculations with discounts
- **Ages 12-14**: Fraction Story (Hard) - Fraction and money word problems
- **Ages 15+**: Complex Business Math (Hard) - Business calculations with costs and revenue

## Backend Implementation

### 1. API Endpoints Added
- **`GET /api/mathematical-comprehension-tasks/<user_id>`**: Fetches age-appropriate mathematical comprehension tasks
- **`GET /api/mathematical-comprehension-task/<task_id>`**: Gets a specific mathematical comprehension task by ID
- **`POST /api/start-mathematical-comprehension-task`**: Marks a mathematical comprehension task as started

### 2. Route Updates
- **`/task4.html`**: Now requires user authentication and passes user_id to template

### 3. Database Integration
- Fetches user age from `demographics` table
- Queries `mathematical_comprehension_tasks` table based on age range
- Updates `user_tasks` table when tasks are started

## Frontend Implementation

### 1. Task4.html - Task Selection Page
- **Welcome Section**: Personalized greeting with user's age
- **Loading State**: Spinner while fetching tasks
- **Error State**: Handles API errors gracefully
- **Task Grid**: Displays age-appropriate mathematical comprehension tasks
- **No Tasks State**: When no tasks match user's age

### 2. Task Cards Features
- **Difficulty Indicators**: Color-coded (Green=Easy, Yellow=Medium, Red=Hard)
- **Task Information**: Name, instructions, problem preview, estimated time
- **Problem Preview**: Scrollable problem text area
- **Action Buttons**: Start Task and Preview

### 3. Interactive Features
- **Task Preview Modal**: Full-screen preview of mathematical problem and questions
- **Start Task**: Marks task as "In Progress" and redirects to task44.html
- **Responsive Design**: Works on all device sizes

## File Structure

### New Files
- `create_mathematical_comprehension_tasks_table.sql` - Database setup script
- `MATHEMATICAL_COMPREHENSION_SETUP.md` - This setup guide

### Modified Files
- `app.py` - Added mathematical comprehension tasks API endpoints
- `templates/task4.html` - Complete UI overhaul with age-based tasks
- `templates/task44.html` - Updated to load dynamic task content

## How It Works

### 1. User Access Flow
1. User navigates to `/task4.html`
2. System checks if user is logged in
3. Fetches user's age from demographics table
4. Queries mathematical_comprehension_tasks table for age-appropriate tasks
5. Displays personalized task cards

### 2. Task Selection
1. User sees tasks filtered by their age
2. Each task shows difficulty level, instructions, problem preview, and estimated time
3. User can preview full problem and questions in a modal
4. Clicking "Start Task" marks task as started
5. User is redirected to task44.html for actual problem solving

### 3. Task Execution
1. Task44.html extracts task_id from URL parameters
2. Fetches specific task content from database
3. Dynamically displays mathematical problem and questions
4. User reads problem and answers questions
5. Progress can be saved or task can be submitted

### 4. Age-Based Filtering
- **6-8 years**: Simple counting and sharing problems
- **9-11 years**: Money problems with basic calculations
- **12-14 years**: Fraction and money word problems
- **15+ years**: Complex business math with multiple concepts

## Task Features

### 1. Question Types
- **Multiple Choice**: Questions 1 and 2 can be multiple choice with options stored as JSON
- **Number Input**: Questions can require numerical answers
- **Text Input**: Questions can require text explanations

### 2. Difficulty Levels
- **Easy**: Simple counting and basic operations
- **Medium**: Money problems and discounts
- **Hard**: Fractions, complex calculations, and business math

### 3. Time Estimates
- Each task includes estimated completion time
- Helps users plan their work
- Based on age-appropriate problem-solving speed

## Testing

### 1. Database Setup
```sql
-- Verify table creation
USE dyslexia_study;
SHOW TABLES LIKE 'mathematical_comprehension_tasks';
SELECT * FROM mathematical_comprehension_tasks;
```

### 2. User Profile Requirements
- User must have completed profile setup
- Age must be recorded in demographics table
- User must be logged in to access task4.html

### 3. Test Scenarios
- **Valid age**: Should show appropriate tasks
- **Missing age**: Should show default tasks with message
- **No matching tasks**: Should show "no tasks" state
- **Task start**: Should update user_tasks table
- **Task execution**: Should load correct content and questions

## Customization

### 1. Adding New Age Groups
```sql
INSERT INTO mathematical_comprehension_tasks (task_name, age_min, age_max, difficulty_level, problem_text, question1, question2, question3, answer1_options, answer2_options, answer3_type, instructions) 
VALUES ('New Task Name', 5, 6, 'Easy', 'Problem text here', 'Question 1', 'Question 2', 'Question 3', '["option1", "option2"]', '["option1", "option2"]', 'number', 'Instructions here');
```

### 2. Modifying Task Content
```sql
UPDATE mathematical_comprehension_tasks 
SET problem_text = 'New problem text', 
    question1 = 'New question 1',
    question2 = 'New question 2',
    question3 = 'New question 3',
    instructions = 'New instructions'
WHERE id = 1;
```

### 3. Adding New Difficulty Levels
```sql
-- First modify the ENUM in the table
ALTER TABLE mathematical_comprehension_tasks 
MODIFY COLUMN difficulty_level ENUM('Easy', 'Medium', 'Hard', 'Expert') NOT NULL;
```

## Integration with Existing System

### 1. Task Progress Tracking
- Uses existing `user_tasks` table
- Integrates with dashboard progress display
- Maintains consistency with other task types

### 2. User Authentication
- Requires login like other tasks
- Uses session management
- Redirects to login if not authenticated

### 3. Accessibility Features
- Maintains all existing accessibility options
- Font size controls, dyslexic font, etc.
- Consistent with other task pages

## Troubleshooting

### 1. Common Issues
- **No tasks showing**: Check if mathematical_comprehension_tasks table exists and has data
- **Age not working**: Verify demographics table has user age
- **Task not loading**: Check if task_id is being passed correctly

### 2. Debug Steps
1. Check browser console for JavaScript errors
2. Verify API endpoints are responding correctly
3. Check database connection and table structure
4. Ensure user is logged in and has proper session

### 3. Database Queries for Debugging
```sql
-- Check if user has age recorded
SELECT age, date_of_birth FROM demographics WHERE user_id = [USER_ID];

-- Check available tasks for specific age
SELECT * FROM mathematical_comprehension_tasks WHERE age_min <= [AGE] AND age_max >= [AGE];

-- Check user task status
SELECT * FROM user_tasks WHERE user_id = [USER_ID] AND task_name LIKE '%Mathematical%';
```

## Mathematical Problem Examples

### Ages 6-8: Simple Counting
- Problem: Tom has 5 red apples and 3 green apples. His friend Sarah gives him 2 more red apples.
- Questions: How many red apples does Tom have now? How many total apples? How many if shared equally?

### Ages 9-11: Money Problems
- Problem: A toy store sells action figures for $8 each and board games for $15 each. They sold 6 action figures and 3 board games with a $2 discount.
- Questions: How much money from action figures? How much from board games? Total money earned?

### Ages 12-14: Fraction Story
- Problem: A pizza restaurant sells large pizzas cut into 12 slices. They sold 8 whole pizzas and 3/4 of another pizza at $2.50 per slice.
- Questions: How many slices sold? How much money earned? How many slices in special deal?

### Ages 15+: Complex Business Math
- Problem: A coffee shop has fixed costs of $2,000 per month and variable costs of $1.50 per coffee. They sell coffee for $4.50 each and sold 800 coffees last month.
- Questions: What were total costs? How much profit? How many coffees needed for $3,000 profit?
