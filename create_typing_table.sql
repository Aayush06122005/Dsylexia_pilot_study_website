-- Create typing_progress table for storing typing task data
CREATE TABLE IF NOT EXISTS typing_progress (
    user_id INT NOT NULL,
    text TEXT,
    keystrokes LONGTEXT,
    timer INT,
    updated_at DATETIME,
    PRIMARY KEY (user_id)
); 