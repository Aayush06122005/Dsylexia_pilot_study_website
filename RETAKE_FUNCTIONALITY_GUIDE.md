# Retake Functionality Implementation Guide

## Overview

This guide explains how to implement consistent retake functionality across all task types in the dyslexia research study website. The retake functionality allows users to retake completed tasks while preserving their previous submissions.

## Key Components

### 1. Backend API Endpoints

#### `/api/retake-task` (POST)
- **Purpose**: Resets a task status to "In Progress" for retaking
- **Input**: `task_name` in JSON body
- **Output**: Success message confirming task reset
- **Preservation**: Previous submissions are preserved in the database

#### `/api/get-task-status` (GET)
- **Purpose**: Get the current status of any task for the current user
- **Input**: `task_name` as query parameter
- **Output**: Task status ("Not Started", "In Progress", "Completed")

#### Progress Loading Endpoints (Task-specific)
- `/api/get-saved-progress` - For reading tasks (audio recordings)
- `/api/get-typing-progress` - For typing tasks (text, keystrokes, timer)
- `/api/get-comprehension-progress` - For comprehension tasks (answers)
- `/api/get-aptitude-progress` - For aptitude tasks (answers, section progress)
- `/api/get-writing-progress` - For writing tasks (image uploads)

### 2. Frontend Implementation Pattern

#### Dashboard Retake Button Logic
```javascript
// In participant-dashboard.html
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('task-btn')) {
        const taskName = e.target.getAttribute('data-task');
        const status = e.target.getAttribute('data-status');
        
        // For retakes (when status is "Completed"), first reset the task status
        if (status === 'Completed') {
            fetch('/api/retake-task', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ task_name: taskName })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    // Navigate to task page with retake parameter
                    const page = getTaskPage(taskName);
                    if (page) {
                        window.location.href = '/' + page + '?retake=true';
                    }
                } else {
                    alert(data.message || 'Failed to reset task for retake');
                }
            })
            .catch(error => {
                console.error('Error resetting task:', error);
                alert('Error resetting task. Please try again.');
            });
        } else {
            // For non-completed tasks, navigate directly
            const page = getTaskPage(taskName);
            if (page) {
                window.location.href = '/' + page;
            }
        }
    }
});
```

#### Task Page Retake Handling
```javascript
// Standard pattern for all task pages
document.addEventListener('DOMContentLoaded', function() {
    // Check if this is a retake
    const urlParams = new URLSearchParams(window.location.search);
    const isRetake = urlParams.get('retake') === 'true';
    
    if (isRetake) {
        // Show retake notification
        const notificationDiv = document.createElement('div');
        notificationDiv.className = 'bg-blue-100 border-l-4 border-blue-500 text-blue-700 p-4 mb-4';
        notificationDiv.innerHTML = `
            <p class="font-bold">Retake Mode</p>
            <p>You are retaking this task. Your previous submission has been preserved.</p>
        `;
        
        // Insert notification at the top of content
        const contentWrapper = document.querySelector('.content-wrapper');
        if (contentWrapper) {
            contentWrapper.insertBefore(notificationDiv, contentWrapper.firstChild);
        }
    }
    
    // Load task content
    loadTaskContent();
    
    // Check task status and load progress
    checkTaskStatusAndLoadProgress();
});

function checkTaskStatusAndLoadProgress() {
    const urlParams = new URLSearchParams(window.location.search);
    const isRetake = urlParams.get('retake') === 'true';
    
    if (!isRetake) {
        // Only check completion status if not in retake mode
        fetch('/api/user-tasks')
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                const task = data.tasks.find(t => t.task_name === 'TASK_NAME');
                if (task && task.status === 'Completed') {
                    alert('This task has already been completed. Redirecting to dashboard.');
                    window.location.href = '/participant-dashboard';
                    return;
                }
            }
        })
        .catch(() => {
            console.log('Could not check task status');
        });
    }

    // Load saved progress (always check, even in retake mode)
    loadSavedProgress();
}
```

### 3. Task-Specific Implementation

#### Reading Tasks (task11.html)
- **Progress Type**: Audio recordings
- **Loading**: Uses `/api/get-saved-progress`
- **Preservation**: Previous audio files are kept in uploads folder

#### Typing Tasks (task22.html)
- **Progress Type**: Text content, keystrokes, timer
- **Loading**: Uses `/api/get-typing-progress`
- **Preservation**: Previous typing data is kept in database

#### Comprehension Tasks (task_verbal_test.html, task_mathematic_comprehension.html)
- **Progress Type**: Question answers
- **Loading**: Uses `/api/get-comprehension-progress`
- **Preservation**: Previous answers are kept in database

#### Aptitude Tasks (aptitude.html)
- **Progress Type**: Section answers, current section, progress percentage
- **Loading**: Uses `/api/get-aptitude-progress`
- **Preservation**: Previous answers and progress are kept in database

#### Writing Tasks (task5.html, task55.html)
- **Progress Type**: Image uploads
- **Loading**: Uses `/api/get-writing-progress`
- **Preservation**: Previous image files are kept in uploads folder

### 4. Database Schema Requirements

#### User Tasks Table
```sql
CREATE TABLE user_tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    task_name VARCHAR(255) NOT NULL,
    status ENUM('Not Started', 'In Progress', 'Completed') DEFAULT 'Not Started',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_user_task (user_id, task_name)
);
```

#### Progress Tables (Task-specific)
Each task type has its own progress table to store detailed progress data:

- `audio_recordings` - For reading tasks
- `typing_progress` - For typing tasks  
- `comprehension_progress` - For comprehension tasks
- `aptitude_progress` - For aptitude tasks
- `writing_samples` - For writing tasks

### 5. Implementation Checklist

#### For Each Task Type:

1. **Backend**:
   - [ ] Ensure progress loading endpoint exists
   - [ ] Ensure progress saving endpoint exists
   - [ ] Ensure task completion endpoint exists

2. **Frontend**:
   - [ ] Add retake notification display
   - [ ] Add progress loading logic
   - [ ] Add task status checking (with retake bypass)
   - [ ] Add progress restoration in UI

3. **Testing**:
   - [ ] Test retake button functionality
   - [ ] Test progress loading for retakes
   - [ ] Test progress preservation
   - [ ] Test completion after retake

### 6. Common Patterns

#### Progress Loading Pattern
```javascript
function loadSavedProgress() {
    fetch('/api/get-[TASK_TYPE]-progress')
    .then(res => res.json())
    .then(data => {
        if (data.success && data.progress) {
            // Restore progress data
            restoreProgress(data.progress);
            
            // Show success notification
            showProgressLoadedNotification();
        }
    })
    .catch(error => {
        console.log('Could not load saved progress:', error);
    });
}
```

#### Progress Saving Pattern
```javascript
function saveProgress() {
    const progressData = collectProgressData();
    
    fetch('/api/save-[TASK_TYPE]-progress', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(progressData)
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            showSaveSuccessNotification();
        } else {
            showSaveErrorNotification(data.message);
        }
    })
    .catch(error => {
        showSaveErrorNotification('Network error');
    });
}
```

### 7. Error Handling

#### Common Error Scenarios:
1. **Network errors**: Show user-friendly error messages
2. **Invalid task status**: Redirect to dashboard with explanation
3. **Progress loading failures**: Continue with fresh start
4. **Save failures**: Allow retry with clear feedback

#### Error Handling Pattern:
```javascript
function handleError(error, context) {
    console.error(`Error in ${context}:`, error);
    
    if (error.name === 'NetworkError') {
        alert('Network error. Please check your connection and try again.');
    } else if (error.response && error.response.status === 401) {
        alert('Session expired. Please log in again.');
        window.location.href = '/signin';
    } else {
        alert('An unexpected error occurred. Please try again.');
    }
}
```

## Summary

The retake functionality ensures that:
1. Users can retake completed tasks
2. Previous submissions are preserved
3. Progress is loaded when available
4. The UI clearly indicates retake mode
5. All task types follow consistent patterns

This implementation provides a seamless user experience while maintaining data integrity for research purposes. 