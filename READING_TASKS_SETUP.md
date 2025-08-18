# Age-Based Reading Tasks Setup Guide

## Overview
This implementation adds age-based reading tasks to the task1.html page. Users will see different reading tasks based on their age, making the experience personalized and appropriate for their reading level.

## Database Setup

### 1. Create the reading_tasks table
Run the SQL script `create_reading_tasks_table.sql`:

```sql
-- Run this in your MySQL database
source create_reading_tasks_table.sql;
```

This will create the table and insert sample tasks for different age groups:
- **Ages 6-8**: Simple words (Easy)
- **Ages 9-11**: Short sentences (Medium)  
- **Ages 12-14**: Paragraph reading (Hard)
- **Ages 15+**: Complex passages (Hard)

## Backend Implementation

### 1. API Endpoints Added
- **`GET /api/reading-tasks/<user_id>`**: Fetches age-appropriate reading tasks
- **`POST /api/start-reading-task`**: Marks a reading task as started

### 2. Route Updates
- **`/task1.html`**: Now requires user authentication and passes user_id to template

### 3. Database Integration
- Fetches user age from `demographics` table
- Queries `reading_tasks` table based on age range
- Updates `user_tasks` table when tasks are started

## Frontend Implementation

### 1. New UI Components
- **Welcome Section**: Personalized greeting with user's age
- **Loading State**: Spinner while fetching tasks
- **Error State**: Handles API errors gracefully
- **Task Grid**: Displays age-appropriate reading tasks
- **No Tasks State**: When no tasks match user's age

### 2. Task Cards Features
- **Difficulty Indicators**: Color-coded (Green=Easy, Yellow=Medium, Red=Hard)
- **Task Information**: Name, instructions, estimated time
- **Content Preview**: Scrollable content area
- **Action Buttons**: Start Reading and Preview

### 3. Interactive Features
- **Task Preview Modal**: Full-screen preview of reading content
- **Start Task**: Marks task as "In Progress" and redirects to task11.html
- **Responsive Design**: Works on all device sizes

## File Structure

### New Files
- `create_reading_tasks_table.sql` - Database setup script
- `READING_TASKS_SETUP.md` - This setup guide

### Modified Files
- `app.py` - Added reading tasks API endpoints
- `templates/task1.html` - Complete UI overhaul with age-based tasks

## How It Works

### 1. User Access Flow
1. User navigates to `/task1.html`
2. System checks if user is logged in
3. Fetches user's age from demographics table
4. Queries reading_tasks table for age-appropriate tasks
5. Displays personalized task cards

### 2. Task Selection
1. User sees tasks filtered by their age
2. Each task shows difficulty level, instructions, and content
3. User can preview full content in a modal
4. Clicking "Start Reading" marks task as started
5. User is redirected to task11.html for actual reading

### 3. Age-Based Filtering
- **6-8 years**: Simple word lists for early readers
- **9-11 years**: Short sentences for developing readers
- **12-14 years**: Paragraphs for intermediate readers
- **15+ years**: Complex passages for advanced readers

## Testing

### 1. Database Setup
```sql
-- Verify table creation
USE dyslexia_study;
SHOW TABLES LIKE 'reading_tasks';
SELECT * FROM reading_tasks;
```

### 2. User Profile Requirements
- User must have completed profile setup
- Age must be recorded in demographics table
- User must be logged in to access task1.html

### 3. Test Scenarios
- **Valid age**: Should show appropriate tasks
- **Missing age**: Should show error message
- **No matching tasks**: Should show "no tasks" state
- **Task start**: Should update user_tasks table

## Customization

### 1. Adding New Age Groups
```sql
INSERT INTO reading_tasks (task_name, age_min, age_max, difficulty_level, content, instructions) 
VALUES ('New Task Name', 5, 6, 'Easy', 'Content here', 'Instructions here');
```

### 2. Modifying Task Content
```sql
UPDATE reading_tasks 
SET content = 'New content', instructions = 'New instructions' 
WHERE id = 1;
```

### 3. Adjusting Difficulty Levels
- Easy: Simple words, short content
- Medium: Sentences, moderate complexity
- Hard: Paragraphs, complex vocabulary

## Error Handling

### 1. User Not Logged In
- Redirects to signin page
- Prevents unauthorized access

### 2. Age Not Found
- Shows helpful error message
- Links to profile setup page

### 3. API Failures
- Graceful error display
- Retry functionality
- User-friendly error messages

## Integration Points

### 1. Existing Systems
- **User Authentication**: Session-based login required
- **Profile Management**: Demographics table integration
- **Task Management**: user_tasks table updates
- **Navigation**: Seamless flow to task11.html

### 2. Future Enhancements
- **Progress Tracking**: Save reading progress
- **Scoring System**: Rate reading performance
- **Adaptive Difficulty**: Adjust based on performance
- **Audio Recording**: Integrate with existing audio system

## Notes

- The system automatically handles age-based task filtering
- All tasks are dyslexia-friendly with clear formatting
- Responsive design works on all devices
- Error states provide helpful guidance to users
- Integration with existing task management system

