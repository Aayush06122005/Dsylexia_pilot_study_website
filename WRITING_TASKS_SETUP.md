# Writing Tasks Setup Guide

This guide explains how to set up and use the age-based writing tasks system with image upload functionality.

## Overview

The writing tasks system allows users to:
- View age-appropriate writing tasks based on their demographic information
- Read writing prompts and instructions
- Write responses by hand on paper
- Upload photos of their handwritten work
- Save progress and submit completed tasks

## Database Setup

### 1. Create Writing Tasks Table

Run the SQL script `create_writing_tasks_table.sql` to create the database table and populate it with sample tasks:

```sql
-- Create writing_tasks table for age-based writing tasks
USE dyslexia_study;

CREATE TABLE IF NOT EXISTS writing_tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    task_name VARCHAR(255) NOT NULL,
    age_min INT NOT NULL,
    age_max INT NOT NULL,
    difficulty_level ENUM('Easy', 'Medium', 'Hard') NOT NULL,
    prompt TEXT NOT NULL,
    instructions TEXT,
    word_limit_min INT DEFAULT 20,
    word_limit_max INT DEFAULT 100,
    estimated_time INT DEFAULT 10,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample writing tasks for different age groups
INSERT INTO writing_tasks (task_name, age_min, age_max, difficulty_level, prompt, instructions, word_limit_min, word_limit_max, estimated_time) VALUES
('Simple Sentences (Ages 6-8)', 6, 8, 'Easy', 'Write about your favorite toy. Tell us what it looks like and why you like to play with it.', 'Write simple sentences about your favorite toy. Use words you know how to spell. Try to write at least 3-4 sentences.', 20, 50, 8),
('Short Story (Ages 9-11)', 9, 11, 'Medium', 'Write a short story about a magical pet. What would happen if you had a pet that could do something special?', 'Write a short story with a beginning, middle, and end. Include characters and describe what happens. Try to make it interesting!', 50, 100, 12),
('Personal Essay (Ages 12-14)', 12, 14, 'Hard', 'Write an essay about a time when you helped someone. What did you do and how did it make you feel?', 'Write a well-structured essay with an introduction, body paragraphs, and conclusion. Use descriptive language and explain your thoughts clearly.', 100, 200, 15),
('Analytical Writing (Ages 15+)', 15, 99, 'Hard', 'Write an essay discussing the importance of reading in modern life. Consider both traditional books and digital reading, and provide examples to support your arguments.', 'Write a formal essay with a clear thesis statement, well-developed arguments, and supporting evidence. Use academic language and proper essay structure.', 200, 400, 20);
```

## Backend Implementation

### 1. API Endpoints Added

The following new API endpoints have been added to `app.py`:

#### Get Age-Appropriate Writing Tasks
```python
@app.route('/api/writing-tasks/<int:user_id>', methods=['GET'])
def get_writing_tasks(user_id):
    """Get age-appropriate writing tasks for a user"""
```

#### Get Specific Writing Task
```python
@app.route('/api/writing-task/<int:task_id>', methods=['GET'])
def get_writing_task(task_id):
    """Get a specific writing task by ID"""
```

#### Start Writing Task
```python
@app.route('/api/start-writing-task', methods=['POST'])
def start_writing_task():
    """Mark a writing task as started"""
```

#### Save Writing Progress
```python
@app.route('/api/save-writing-progress', methods=['POST'])
def save_writing_progress():
    """Save writing progress with image upload"""
```

#### Upload Writing (Submit)
```python
@app.route('/api/upload-writing', methods=['POST'])
def upload_writing():
    """Submit completed writing task with image"""
```

### 2. File Upload Configuration

The system has been updated to support image file uploads:

- **Allowed Extensions**: Added image formats (jpg, jpeg, png, gif, bmp, tiff, webp) to `ALLOWED_EXTENSIONS`
- **File Size Limit**: 10MB maximum
- **Upload Directory**: Files are saved to the `uploads/` directory

## Frontend Implementation

### 1. Task Selection Page (`task5.html`)

Features:
- Age-based task filtering
- Task cards with difficulty indicators
- Preview modal for task details
- Responsive design with accessibility features
- Loading states and error handling

### 2. Task Execution Page (`task55.html`)

Features:
- Dynamic task content loading
- Writing prompt display
- Step-by-step instructions
- Image upload with drag-and-drop support
- File validation and preview
- Progress saving and task submission
- Accessibility panel with font controls, dyslexic font, etc.

### 3. Image Upload Functionality

- **Drag and Drop**: Users can drag image files directly onto the upload area
- **Click to Upload**: Traditional file picker interface
- **File Validation**: Checks file type and size
- **Image Preview**: Shows uploaded image before submission
- **Remove Option**: Allows users to remove and re-upload images

## Routes Added

### 1. Task Selection Route
```python
@app.route('/task5.html')
def task5():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('signin'))
    return render_template('task5.html', user_id=user_id)
```

### 2. Task Execution Route
```python
@app.route('/task55.html')
def task55():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('signin'))
    return render_template('task55.html', user_id=user_id)
```

## Dashboard Integration

The participant dashboard has been updated to correctly route "Writing Task" to `task5.html`:

```javascript
if (taskName === 'Writing Task') return 'task5.html';
```

## Task Features

### 1. Age-Based Filtering
- Tasks are automatically filtered based on user's age from demographics table
- Age ranges: 6-8, 9-11, 12-14, 15+
- Appropriate difficulty levels for each age group

### 2. Writing Prompts
- **Ages 6-8**: Simple sentence writing about familiar topics
- **Ages 9-11**: Short story creation with basic narrative structure
- **Ages 12-14**: Personal essay writing with reflection
- **Ages 15+**: Analytical essay writing with formal structure

### 3. Progress Tracking
- Tasks are marked as "In Progress" when started
- Progress can be saved with uploaded images
- Completed tasks are marked as "Completed" in user_tasks table

## File Storage

### 1. Upload Directory Structure
```
uploads/
├── writing_samples/
│   ├── user_1/
│   │   ├── task_1_image.jpg
│   │   └── task_2_image.png
│   └── user_2/
│       └── task_1_image.jpg
```

### 2. File Naming Convention
- Files are saved with unique names to prevent conflicts
- Original file extensions are preserved
- User and task information is included in the file path

## Testing Instructions

### 1. Database Setup
1. Run the `create_writing_tasks_table.sql` script
2. Verify the table was created and populated with sample data

### 2. Backend Testing
1. Start the Flask application
2. Test API endpoints with sample user data
3. Verify file upload functionality works correctly

### 3. Frontend Testing
1. Navigate to the participant dashboard
2. Click on "Writing Task" to access task selection
3. Select a task and verify the preview modal works
4. Start a task and test the image upload functionality
5. Verify progress saving and task submission work correctly

### 4. Age-Based Testing
1. Test with users of different ages
2. Verify that appropriate tasks are shown for each age group
3. Check that task difficulty matches age expectations

## Accessibility Features

The writing tasks include the same accessibility features as other tasks:
- Font size controls (A-, Reset, A+)
- Dyslexic font toggle
- Monochrome mode
- Reading ruler
- Big cursor option
- High contrast design

## Error Handling

The system includes comprehensive error handling for:
- File upload failures
- Invalid file types or sizes
- Database connection issues
- Missing task data
- User authentication problems

## Security Considerations

- File type validation prevents malicious uploads
- File size limits prevent server overload
- User authentication required for all operations
- Session-based user identification
- Secure file storage with proper permissions

## Future Enhancements

Potential improvements for the writing tasks system:
- OCR (Optical Character Recognition) for automatic text extraction
- Handwriting analysis features
- Multiple image upload support for multi-page writing
- Real-time collaboration features
- Advanced analytics and reporting
- Integration with educational assessment tools
