# Task11.html Integration Guide

## Overview
Task11.html now dynamically displays reading content from the `reading_tasks` table instead of hardcoded content. Users select a task from task1.html and are redirected to task11.html with the specific content to read.

## How It Works

### 1. User Flow
1. **User visits `/task1.html`** → Sees age-appropriate reading tasks
2. **User selects a task** → Clicks "Start Reading" button
3. **System redirects to `/task11.html?task_id=X`** → X is the task ID
4. **Task11.html loads** → Fetches content for task ID X from database
5. **Content displays** → User sees specific reading material to record

### 2. Data Flow
```
task1.html → API call → reading_tasks table → task11.html → Display content
     ↓              ↓              ↓              ↓
  Show tasks    Start task    Fetch content   Read & record
```

## Backend Changes

### 1. New API Endpoint
```python
@app.route('/api/reading-task/<int:task_id>', methods=['GET'])
def get_reading_task_by_id(task_id):
    """Get a specific reading task by ID"""
```

### 2. Updated Route
```python
@app.route('/task11.html')
def task11():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('signin'))
    return render_template('task11.html', user_id=user_id)
```

### 3. Task1.html Updates
- Modified `startReadingTask()` function to pass task ID in URL
- Redirects to `task11.html?task_id=X`

## Frontend Changes

### 1. Task11.html Modifications
- **Dynamic content loading** instead of hardcoded story
- **Task ID extraction** from URL parameters
- **API integration** to fetch reading content
- **Error handling** for missing or invalid tasks

### 2. New JavaScript Functions
```javascript
function loadReadingContent() {
    // Extract task_id from URL and fetch content
}

function displayReadingContent(task) {
    // Display task instructions, content, and metadata
}

function showError(message) {
    // Show error state with back button
}
```

### 3. Content Display Structure
```html
<div id="readingContent">
    <!-- Instructions section -->
    <!-- Content to read section -->
    <!-- Difficulty and time info -->
</div>
```

## Database Integration

### 1. Required Tables
- **`reading_tasks`** - Stores reading task content
- **`user_tasks`** - Tracks user progress
- **`users`** - User authentication
- **`demographics`** - User age information

### 2. Sample Reading Task Data
```sql
INSERT INTO reading_tasks (task_name, age_min, age_max, difficulty_level, content, instructions, estimated_time) VALUES
('Simple Words (Ages 6-8)', 6, 8, 'Easy', 'cat, dog, run, jump, play, book, tree, house, ball, sun, moon, star, fish, bird, car, bus', 'Read each word clearly and slowly. Take your time with each word.', 5);
```

## Testing the Integration

### 1. Database Setup
```sql
-- Run the setup script
source create_reading_tasks_table.sql;

-- Verify data exists
SELECT * FROM reading_tasks;
```

### 2. Test User Flow
1. **Login as a user**
2. **Navigate to `/task1.html`**
3. **Select a reading task**
4. **Click "Start Reading"**
5. **Verify redirect to `/task11.html?task_id=X`**
6. **Check content loads correctly**

### 3. Error Scenarios
- **No task_id parameter** → Shows error with back button
- **Invalid task_id** → Shows "task not found" error
- **Database connection failure** → Shows connection error
- **Missing user authentication** → Redirects to signin

## Customization Options

### 1. Content Formatting
- **Instructions styling** - Modify CSS classes in `displayReadingContent()`
- **Content layout** - Adjust HTML structure in the template
- **Difficulty indicators** - Add color coding or icons

### 2. Additional Metadata
- **Task category** - Add subject or topic fields
- **Learning objectives** - Include educational goals
- **Prerequisites** - List required skills

### 3. Enhanced Features
- **Progress tracking** - Save reading attempts
- **Scoring system** - Rate reading performance
- **Adaptive content** - Adjust difficulty based on performance

## Troubleshooting

### 1. Common Issues
- **"No task selected"** → Check URL parameters and task1.html redirect
- **"Failed to load reading task"** → Verify API endpoint and database
- **"Task not found"** → Check task_id exists in reading_tasks table

### 2. Debug Steps
1. **Check browser console** for JavaScript errors
2. **Verify Flask console** for backend errors
3. **Test API endpoint** directly: `/api/reading-task/1`
4. **Check database** for task data existence

### 3. Database Verification
```sql
-- Check if table exists
SHOW TABLES LIKE 'reading_tasks';

-- Check if data exists
SELECT COUNT(*) FROM reading_tasks;

-- Check specific task
SELECT * FROM reading_tasks WHERE id = 1;
```

## Security Considerations

### 1. Authentication
- **User must be logged in** to access task11.html
- **Session validation** prevents unauthorized access
- **User ID verification** ensures proper task access

### 2. Data Validation
- **Task ID validation** prevents SQL injection
- **User ownership** ensures users only see their tasks
- **Input sanitization** prevents XSS attacks

## Performance Optimization

### 1. Caching
- **Task content caching** for frequently accessed tasks
- **User session caching** to reduce database queries
- **Static content optimization** for better load times

### 2. Database Optimization
- **Indexed queries** on task_id and user_id
- **Connection pooling** for better database performance
- **Query optimization** for faster content retrieval

## Future Enhancements

### 1. Advanced Features
- **Multiple content types** (text, images, audio)
- **Interactive elements** (highlighting, annotations)
- **Progress analytics** (reading speed, accuracy)

### 2. Integration Points
- **Learning management system** integration
- **Assessment tools** for reading evaluation
- **Parent/teacher dashboard** for progress monitoring

## Notes
- The system automatically handles task selection and content loading
- All content is dyslexia-friendly with accessibility features
- Error states provide helpful guidance to users
- Integration maintains existing audio recording functionality
