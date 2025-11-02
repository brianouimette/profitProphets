-- MySQL HeatWave Schema for NBA Fantasy Optimizer
-- Oracle Cloud Free Tier Setup

-- Create database
CREATE DATABASE IF NOT EXISTS nba_fantasy;
USE nba_fantasy;

-- Teams table
CREATE TABLE teams (
    id INT PRIMARY KEY,
    abbreviation VARCHAR(10) NOT NULL,
    city VARCHAR(100),
    name VARCHAR(100),
    conference VARCHAR(20),
    division VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Players table
CREATE TABLE players (
    id INT PRIMARY KEY,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    position ENUM('PG', 'SG', 'SF', 'PF', 'C'),
    team_id INT,
    jersey_number INT,
    height VARCHAR(10),
    weight INT,
    birth_date DATE,
    country VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE SET NULL
);

-- Games table
CREATE TABLE games (
    id INT PRIMARY KEY,
    game_date DATE NOT NULL,
    home_team_id INT NOT NULL,
    away_team_id INT NOT NULL,
    home_score INT,
    away_score INT,
    status VARCHAR(20) DEFAULT 'SCHEDULED',
    season VARCHAR(10),
    game_type VARCHAR(20) DEFAULT 'REGULAR',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (home_team_id) REFERENCES teams(id),
    FOREIGN KEY (away_team_id) REFERENCES teams(id),
    INDEX idx_game_date (game_date),
    INDEX idx_season (season),
    INDEX idx_teams (home_team_id, away_team_id)
);

-- Player game logs table
CREATE TABLE player_game_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    player_id INT NOT NULL,
    game_id INT NOT NULL,
    fantasy_points DECIMAL(10,2),
    minutes_played INT,
    field_goals_made INT,
    field_goals_attempted INT,
    three_pointers_made INT,
    three_pointers_attempted INT,
    free_throws_made INT,
    free_throws_attempted INT,
    rebounds INT,
    assists INT,
    steals INT,
    blocks INT,
    turnovers INT,
    personal_fouls INT,
    plus_minus INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE,
    FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE CASCADE,
    INDEX idx_player_game (player_id, game_id),
    INDEX idx_game_date (game_id),
    INDEX idx_fantasy_points (fantasy_points)
);

-- Injuries table
CREATE TABLE injuries (
    id INT PRIMARY KEY AUTO_INCREMENT,
    player_id INT NOT NULL,
    injury_type VARCHAR(100),
    status VARCHAR(50) DEFAULT 'ACTIVE',
    start_date DATE,
    expected_return DATE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE,
    INDEX idx_player_injury (player_id),
    INDEX idx_injury_status (status),
    INDEX idx_injury_dates (start_date, expected_return)
);

-- DFS projections table
CREATE TABLE dfs_projections (
    id INT PRIMARY KEY AUTO_INCREMENT,
    player_id INT NOT NULL,
    game_id INT NOT NULL,
    projected_fantasy_points DECIMAL(10,2),
    salary INT,
    ownership_percentage DECIMAL(5,2),
    ceiling DECIMAL(10,2),
    floor DECIMAL(10,2),
    value_score DECIMAL(10,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE,
    FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE CASCADE,
    INDEX idx_player_game_projection (player_id, game_id),
    INDEX idx_salary (salary),
    INDEX idx_value_score (value_score)
);

-- Daily DFS data table
CREATE TABLE daily_dfs_data (
    id INT PRIMARY KEY AUTO_INCREMENT,
    player_id INT NOT NULL,
    game_id INT NOT NULL,
    fantasy_points DECIMAL(10,2),
    salary INT,
    ownership_percentage DECIMAL(5,2),
    slate_id VARCHAR(50),
    platform VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE,
    FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE CASCADE,
    INDEX idx_player_game_daily (player_id, game_id),
    INDEX idx_slate (slate_id),
    INDEX idx_platform (platform)
);

-- Game lineups table
CREATE TABLE game_lineups (
    id INT PRIMARY KEY AUTO_INCREMENT,
    game_id INT NOT NULL,
    team_id INT NOT NULL,
    player_id INT NOT NULL,
    position VARCHAR(10),
    starter BOOLEAN DEFAULT FALSE,
    minutes_played INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE CASCADE,
    FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE,
    FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE,
    INDEX idx_game_team (game_id, team_id),
    INDEX idx_player_lineup (player_id)
);

-- Data sync logs table
CREATE TABLE data_sync_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    sync_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    records_processed INT DEFAULT 0,
    records_updated INT DEFAULT 0,
    records_created INT DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_sync_type (sync_type),
    INDEX idx_status (status),
    INDEX idx_started_at (started_at)
);

-- Create views for analytics
CREATE VIEW v_player_performance AS
SELECT 
    p.id as player_id,
    p.first_name,
    p.last_name,
    p.position,
    t.abbreviation as team,
    AVG(pgl.fantasy_points) as avg_fantasy_points,
    STDDEV(pgl.fantasy_points) as consistency,
    COUNT(pgl.id) as games_played,
    MAX(pgl.fantasy_points) as ceiling,
    MIN(pgl.fantasy_points) as floor
FROM players p
LEFT JOIN player_game_logs pgl ON p.id = pgl.player_id
LEFT JOIN teams t ON p.team_id = t.id
GROUP BY p.id, p.first_name, p.last_name, p.position, t.abbreviation;

CREATE VIEW v_team_defense AS
SELECT 
    t.id as team_id,
    t.abbreviation as team,
    p.position,
    AVG(pgl.fantasy_points) as avg_fantasy_points_allowed,
    STDDEV(pgl.fantasy_points) as defense_consistency,
    COUNT(pgl.id) as games_analyzed
FROM teams t
JOIN games g ON (t.id = g.home_team_id OR t.id = g.away_team_id)
JOIN player_game_logs pgl ON g.id = pgl.game_id
JOIN players p ON pgl.player_id = p.id
WHERE g.status = 'FINAL'
GROUP BY t.id, t.abbreviation, p.position;

-- Create indexes for HeatWave optimization
CREATE INDEX idx_heatwave_analytics ON player_game_logs (player_id, game_id, fantasy_points);
CREATE INDEX idx_heatwave_team_defense ON games (home_team_id, away_team_id, game_date, status);
CREATE INDEX idx_heatwave_player_trends ON player_game_logs (player_id, game_id, created_at);

-- Grant permissions (adjust as needed for your setup)
-- GRANT ALL PRIVILEGES ON nba_fantasy.* TO 'your_username'@'%';
-- FLUSH PRIVILEGES;
