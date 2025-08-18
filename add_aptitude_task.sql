-- Add Aptitude Test to the tasks table
USE dyslexia_study;

INSERT INTO tasks (task_name, description, instructions, estimated_time, devices_required, example) 
VALUES (
    'Aptitude Test',
    'Comprehensive aptitude assessment covering logical reasoning, numerical ability, verbal ability, and spatial reasoning',
    'Complete all four sections of the aptitude test. Each section contains multiple-choice questions. You can save your progress and return later.',
    '45-60 minutes',
    'Computer with internet connection',
    'Sample question: What comes next in the sequence 2, 4, 8, 16, ?'
) ON DUPLICATE KEY UPDATE 
    description = VALUES(description),
    instructions = VALUES(instructions),
    estimated_time = VALUES(estimated_time),
    devices_required = VALUES(devices_required),
    example = VALUES(example);

