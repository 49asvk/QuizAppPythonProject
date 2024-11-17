-- Creating tables needed for application to run well.
-- PostgreSQL installation needed.
CREATE TABLE question_series (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL
);

CREATE TABLE questions (
    id SERIAL PRIMARY KEY,
    series_id INT REFERENCES question_series(id) ON DELETE CASCADE,
    question_text TEXT NOT NULL,
    choice_1 TEXT NOT NULL,
    choice_2 TEXT NOT NULL,
    choice_3 TEXT NOT NULL,
    choice_4 TEXT NOT NULL,
    correct_choice INT NOT NULL CHECK (correct_choice BETWEEN 0 AND 3)
);

CREATE TABLE leaderboard (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    score INT NOT NULL,
    series_id INT REFERENCES question_series(id) ON DELETE CASCADE
);
