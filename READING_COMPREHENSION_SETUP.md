# Age-Based Reading Comprehension Tasks Setup Guide

## Overview
This implementation adds age-based reading comprehension tasks to the task3.html page. Users will see different reading comprehension tasks based on their age, making the experience personalized and appropriate for their reading level.

## Database Setup

### 1. Create the reading_comprehension_tasks table
Run the SQL script `create_reading_comprehension_tasks_table.sql`:

```sql
-- Run this in your MySQL database
source create_reading_comprehension_tasks_table.sql;
```

This will create the table and insert sample tasks for different age groups:
- **Ages 6-8**: Simple Story (Easy) - Basic comprehension with multiple choice questions
- **Ages 9-11**: Short Story (Medium) - Story with character development and events
- **Ages 12-14**: Adventure Story (Hard) - Complex narrative with multiple plot points
- **Ages 15+**: Complex Narrative (Hard) - Advanced text with sophisticated themes

## Backend Implementation

### 1. API Endpoints Added
- **`GET /api/reading-comprehension-tasks/<user_id>`**: Fetches age-appropriate reading comprehension tasks
- **`GET /api/reading-comprehension-task/<task_id>`**: Gets a specific reading comprehension task by ID
- **`POST /api/start-reading-comprehension-task`**: Marks a reading comprehension task as started

### 2. Route Updates
- **`/task3.html`**: Now requires user authentication and passes user_id to template

### 3. Database Integration
- Fetches user age from `demographics` table
- Queries `reading_comprehension_tasks` table based on age range
- Updates `user_tasks` table when tasks are started

## Frontend Implementation

### 1. Task3.html - Task Selection Page
- **Welcome Section**: Personalized greeting with user's age
- **Loading State**: Spinner while fetching tasks
- **Error State**: Handles API errors gracefully
- **Task Grid**: Displays age-appropriate reading comprehension tasks
- **No Tasks State**: When no tasks match user's age

### 2. Task Cards Features
- **Difficulty Indicators**: Color-coded (Green=Easy, Yellow=Medium, Red=Hard)
- **Task Information**: Name, instructions, estimated time
- **Passage Preview**: Scrollable content area showing first 150 characters
- **Action Buttons**: Preview and Start Task

### 3. Interactive Features
- **Task Preview Modal**: Full-screen preview of reading content and questions
- **Start Task**: Marks task as "In Progress" and redirects to task33.html
- **Responsive Design**: Works on all device sizes

### 4. Task33.html - Task Execution Page
- **Dynamic Content Loading**: Loads specific task based on task_id parameter
- **Question Generation**: Automatically creates appropriate input fields based on question type
- **Multiple Choice Support**: Dropdown menus for multiple choice questions
- **Text Input Support**: Text fields for open-ended questions
- **Progress Saving**: Save progress and resume later
- **Task Completion**: Submit answers and mark task as completed

## File Structure

### New Files
- `create_reading_comprehension_tasks_table.sql` - Database setup script
- `READING_COMPREHENSION_SETUP.md` - This setup guide

### Modified Files
- `app.py` - Added reading comprehension tasks API endpoints
- `templates/task3.html` - Complete UI overhaul with age-based task selection
- `templates/task33.html` - Dynamic task execution with question generation

## How It Works

### 1. User Access Flow
1. User navigates to `/task3.html`
2. System checks if user is logged in
3. Fetches user's age from demographics table
4. Queries reading_comprehension_tasks table for age-appropriate tasks
5. Displays personalized task cards

### 2. Task Selection
1. User sees tasks filtered by their age
2. Each task shows difficulty level, instructions, and passage preview
3. User can preview full content and questions in a modal
4. Clicking "Start Task" marks task as started
5. User is redirected to task33.html with task_id parameter

### 3. Task Execution
1. Task33.html extracts task_id from URL parameters
2. Fetches specific task content from database
3. Dynamically generates question inputs based on question type
4. User reads passage and answers questions
5. Progress can be saved or task can be submitted

### 4. Age-Based Filtering
- **6-8 years**: Simple stories with basic comprehension questions
- **9-11 years**: Short stories with character and event questions
- **12-14 years**: Adventure stories with complex plot questions
- **15+ years**: Complex narratives with sophisticated analysis questions

## Question Types

### 1. Multiple Choice Questions
- Questions 1 and 2 are typically multiple choice
- Options stored as JSON in database
- Automatically generates dropdown menus

### 2. Text Input Questions
- Question 3 is typically open-ended
- Generates text input field
- Allows for detailed responses

## Testing

### 1. Database Setup
```sql
-- Verify table creation
USE dyslexia_study;
SHOW TABLES LIKE 'reading_comprehension_tasks';
SELECT * FROM reading_comprehension_tasks;
```

### 2. User Profile Requirements
- User must have completed profile setup
- Age must be recorded in demographics table
- User must be logged in to access task3.html

### 3. Test Scenarios
- **Valid age**: Should show appropriate tasks
- **Missing age**: Should show default tasks with message
- **No matching tasks**: Should show "no tasks" state
- **Task start**: Should update user_tasks table
- **Task execution**: Should load correct content and questions

## Customization

### 1. Adding New Age Groups
```sql
INSERT INTO reading_comprehension_tasks (task_name, age_min, age_max, difficulty_level, passage, question1, question2, question3, answer1_options, answer2_options, answer3_type, instructions) 
VALUES ('New Task Name', 5, 6, 'Easy', 'Content here', 'Question 1', 'Question 2', 'Question 3', '["option1", "option2"]', '["option1", "option2"]', 'text', 'Instructions here');
```

### 2. Modifying Task Content
```sql
UPDATE reading_comprehension_tasks 
SET passage = 'New passage content', 
    question1 = 'New question 1',
    question2 = 'New question 2',
    question3 = 'New question 3'
WHERE id = 1;
```

### 3. Adding More Question Types
To add new question types, modify the `generateQuestionInputs` function in task33.html and add corresponding database fields.

## Error Handling

### 1. Missing Task ID
- Shows error message with "Try Again" and "Back to Tasks" buttons
- Prevents access to task without valid task_id

### 2. Database Connection Issues
- Graceful error handling with user-friendly messages
- Fallback to default tasks when age is not available

### 3. Invalid Age
- Shows message to update profile
- Provides clear guidance on what's needed

## Security Considerations

### 1. User Authentication
- All task pages require user login
- Session validation on all API endpoints

### 2. Data Validation
- Input sanitization for user responses
- SQL injection prevention through parameterized queries

### 3. Access Control
- Users can only access tasks appropriate for their age
- Task content is validated before display

## Performance Optimization

### 1. Database Queries
- Efficient age-based filtering
- Indexed queries for fast task retrieval

### 2. Frontend Loading
- Progressive loading with loading states
- Efficient DOM manipulation for dynamic content

### 3. Caching
- Consider implementing caching for frequently accessed tasks
- Browser caching for static assets

## Future Enhancements

### 1. Additional Question Types
- True/False questions
- Matching questions
- Fill-in-the-blank questions

### 2. Advanced Features
- Timer functionality
- Progress tracking
- Performance analytics

### 3. Accessibility Improvements
- Screen reader compatibility
- Keyboard navigation
- High contrast mode

## Troubleshooting

### Common Issues

1. **Tasks not loading**
   - Check database connection
   - Verify user age in demographics table
   - Check browser console for JavaScript errors

2. **Questions not displaying correctly**
   - Verify JSON format in answer_options fields
   - Check question generation JavaScript

3. **Task submission failing**
   - Check user authentication
   - Verify API endpoint availability
   - Check database permissions

### Debug Mode
Enable debug logging in app.py to see detailed error messages and API calls.
