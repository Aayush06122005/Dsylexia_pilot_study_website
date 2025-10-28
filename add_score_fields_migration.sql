-- Migration script to add score fields to progress tables
-- Run this script to update existing databases

USE dyslexia_study;

-- Add score fields to comprehension_progress table
ALTER TABLE comprehension_progress 
ADD COLUMN IF NOT EXISTS score INT DEFAULT 0,
ADD COLUMN IF NOT EXISTS max_score INT DEFAULT 2;

-- Add score fields to mathematical_comprehension_progress table
ALTER TABLE mathematical_comprehension_progress 
ADD COLUMN IF NOT EXISTS score INT DEFAULT 0,
ADD COLUMN IF NOT EXISTS max_score INT DEFAULT 3;

-- Add max_score field to aptitude_progress table
ALTER TABLE aptitude_progress 
ADD COLUMN IF NOT EXISTS max_score INT DEFAULT 4;

-- Update existing records to have proper max_score values
UPDATE comprehension_progress SET max_score = 2 WHERE max_score = 0;
UPDATE mathematical_comprehension_progress SET max_score = 3 WHERE max_score = 0;
UPDATE aptitude_progress SET max_score = 4 WHERE max_score = 0;

