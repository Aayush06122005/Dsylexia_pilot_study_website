# Age-Based Typing Tasks Setup Guide

## Overview
This implementation adds age-based typing tasks to the task2.html page. Users will see different typing tasks based on their age, making the experience personalized and appropriate for their writing level.

## Database Setup

### 1. Create the typing_tasks table
Run the SQL script `create_typing_tasks_table.sql`:

```sql
-- Run this in your MySQL database
source create_typing_tasks_table.sql;
```

This will create the table and insert sample tasks for different age groups:
- **Ages 6-8**: Simple Sentences (Easy) - Basic writing about favorite animals
- **Ages 9-11**: Short Story (Medium) - Creative story writing with magical themes
- **Ages 12-14**: Personal Essay (Hard) - Reflective writing about challenges
- **Ages 15+**: Analytical Writing (Hard) - Formal essay on technology impact

## Backend Implementation

### 1. API Endpoints Added
- **`GET /api/typing-tasks/<user_id>`**: Fetches age-appropriate typing tasks
- **`GET /api/typing-task/<task_id>`**: Gets a specific typing task by ID
- **`POST /api/start-typing-task`**: Marks a typing task as started

### 2. Route Updates
- **`/task2.html`**: Now requires user authentication and passes user_id to template

### 3. Database Integration
- Fetches user age from `demographics` table
- Queries `typing_tasks` table based on age range
- Updates `user_tasks` table when tasks are started

## Frontend Implementation

### 1. Task2.html - Task Selection Page
- **Welcome Section**: Personalized greeting with user's age
- **Loading State**: Spinner while fetching tasks
- **Error State**: Handles API errors gracefully
- **Task Grid**: Displays age-appropriate typing tasks
- **No Tasks State**: When no tasks match user's age

### 2. Task Cards Features
- **Difficulty Indicators**: Color-coded (Green=Easy, Yellow=Medium, Red=Hard)
- **Task Information**: Name, instructions, word limits, estimated time
- **Prompt Preview**: Scrollable writing prompt area
- **Action Buttons**: Start Typing and Preview

### 3. Interactive Features
- **Task Preview Modal**: Full-screen preview of writing prompt
- **Start Task**: Marks task as "In Progress" and redirects to task22.html
- **Responsive Design**: Works on all device sizes

## File Structure

### New Files
- `create_typing_tasks_table.sql` - Database setup script
- `TYPING_TASKS_SETUP.md` - This setup guide

### Modified Files
- `app.py` - Added typing tasks API endpoints
- `templates/task2.html` - Complete UI overhaul with age-based tasks
- `templates/task22.html` - Updated to load dynamic task content

## How It Works

### 1. User Access Flow
1. User navigates to `/task2.html`
2. System checks if user is logged in
3. Fetches user's age from demographics table
4. Queries typing_tasks table for age-appropriate tasks
5. Displays personalized task cards

### 2. Task Selection
1. User sees tasks filtered by their age
2. Each task shows difficulty level, instructions, word limits, and prompt
3. User can preview full prompt in a modal
4. Clicking "Start Typing" marks task as started
5. User is redirected to task22.html for actual typing

### 3. Task Execution
1. Task22.html extracts task_id from URL parameters
2. Fetches specific task content from database
3. Dynamically displays writing prompt and instructions
4. User types their response with timer and keystroke tracking
5. Progress can be saved or task can be submitted

### 4. Age-Based Filtering
- **6-8 years**: Simple sentences about familiar topics
- **9-11 years**: Creative story writing with imagination
- **12-14 years**: Personal reflection and essay writing
- **15+ years**: Formal analytical writing with structure

## Task Features

### 1. Word Limits
- Each task has minimum and maximum word counts
- Helps users understand expected length
- Appropriate for different age groups

### 2. Difficulty Levels
- **Easy**: Simple topics, basic sentences
- **Medium**: Creative writing, story structure
- **Hard**: Formal writing, complex topics

### 3. Time Estimates
- Each task includes estimated completion time
- Helps users plan their work
- Based on age-appropriate writing speed

## Testing

### 1. Database Setup
```sql
-- Verify table creation
USE dyslexia_study;
SHOW TABLES LIKE 'typing_tasks';
SELECT * FROM typing_tasks;
```

### 2. User Profile Requirements
- User must have completed profile setup
- Age must be recorded in demographics table
- User must be logged in to access task2.html

### 3. Test Scenarios
- **Valid age**: Should show appropriate tasks
- **Missing age**: Should show default tasks with message
- **No matching tasks**: Should show "no tasks" state
- **Task start**: Should update user_tasks table
- **Task execution**: Should load correct content and instructions

## Customization

### 1. Adding New Age Groups
```sql
INSERT INTO typing_tasks (task_name, age_min, age_max, difficulty_level, prompt, instructions, word_limit_min, word_limit_max, estimated_time) 
VALUES ('New Task Name', 5, 6, 'Easy', 'Prompt here', 'Instructions here', 20, 50, 5);
```

### 2. Modifying Task Content
```sql
UPDATE typing_tasks 
SET prompt = 'New prompt text', 
    instructions = 'New instructions',
    word_limit_min = 100,
    word_limit_max = 200
WHERE id = 1;
```

### 3. Adding New Difficulty Levels
```sql
-- First modify the ENUM in the table
ALTER TABLE typing_tasks 
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
- **No tasks showing**: Check if typing_tasks table exists and has data
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
SELECT * FROM typing_tasks WHERE age_min <= [AGE] AND age_max >= [AGE];

-- Check user task status
SELECT * FROM user_tasks WHERE user_id = [USER_ID] AND task_name LIKE '%Typing%';
```
