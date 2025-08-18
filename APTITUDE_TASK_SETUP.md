# Aptitude Task Setup Guide

## Overview
The Aptitude Task has been added to the Dyslexia Research Study website. It includes a comprehensive aptitude test with four sections: Logical Reasoning, Numerical Ability, Verbal Ability, and Spatial Reasoning.

## Database Setup

### 1. Create the aptitude_progress table
Run the SQL script `create_aptitude_table.sql` to create the table for storing aptitude test progress:

```sql
-- Run this in your MySQL database
source create_aptitude_table.sql;
```

### 2. Add the aptitude task to the tasks table
Run the SQL script `add_aptitude_task.sql` to add the aptitude task to the main tasks table:

```sql
-- Run this in your MySQL database
source add_aptitude_task.sql;
```

## Features

### Task Structure
- **Logical Reasoning**: Pattern recognition and logical deduction questions
- **Numerical Ability**: Mathematical problem-solving questions
- **Verbal Ability**: Language comprehension and analogy questions
- **Spatial Reasoning**: Visual and spatial relationship questions

### Functionality
- Progress tracking with visual progress bar
- Save progress functionality
- Section navigation between different test areas
- Automatic scoring calculation
- Integration with the main user task system

## API Endpoints

### Save Progress
- **POST** `/api/save-aptitude-progress`
- Saves current progress and marks task as "In Progress"

### Get Progress
- **GET** `/api/get-aptitude-progress`
- Retrieves saved progress for the current user

### Submit Test
- **POST** `/api/submit-aptitude`
- Submits completed test and marks task as "Completed"

## Files Added/Modified

### New Files
- `templates/aptitude.html` - Main aptitude test interface
- `create_aptitude_table.sql` - Database table creation script
- `add_aptitude_task.sql` - Task addition script
- `APTITUDE_TASK_SETUP.md` - This setup guide

### Modified Files
- `app.py` - Added aptitude API endpoints and route
- `templates/participant-dashboard.html` - Added aptitude task card
- Database schema now includes aptitude_progress table

## Usage

1. Users can access the aptitude test from their participant dashboard
2. The test includes clear instructions and can be completed in sections
3. Progress is automatically saved and can be resumed later
4. Upon completion, the task is marked as completed in the user's task list

## Testing

To test the aptitude task:

1. Ensure all database tables are created
2. Log in as a participant
3. Navigate to the participant dashboard
4. Click on the "Aptitude Test" card
5. Complete the test sections
6. Verify that progress is saved and task status updates correctly

## Notes

- The aptitude test uses the existing math.jpg image as a placeholder
- Scoring is simplified (1 point per answered question)
- The test is designed to be dyslexia-friendly with clear formatting and instructions
- All progress is stored in the database and integrated with the existing task management system

