-- NBA Fantasy Optimizer Database Schema
-- This file contains the complete database schema for the NBA Fantasy Optimizer

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create custom types
CREATE TYPE player_position AS ENUM ('PG', 'SG', 'SF', 'PF', 'C');
CREATE TYPE roster_status AS ENUM ('ROSTER', 'UFA', 'RFA', 'DRAFT', 'INJURED');
CREATE TYPE game_status AS ENUM ('SCHEDULED', 'IN_PROGRESS', 'FINAL', 'POSTPONED', 'CANCELLED');
CREATE TYPE injury_status AS ENUM ('OUT', 'QUESTIONABLE', 'PROBABLE', 'DOUBTFUL');

-- Players table
CREATE TABLE players (
    id BIGINT PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    primary_position player_position NOT NULL,
    alternate_positions player_position[] DEFAULT '{}',
    jersey_number VARCHAR(10),
    current_team_id BIGINT,
    current_roster_status roster_status,
    height VARCHAR(10),
    weight INTEGER,
    birth_date DATE,
    age INTEGER,
    birth_city VARCHAR(100),
    birth_country VARCHAR(50),
    rookie BOOLEAN DEFAULT FALSE,
    high_school VARCHAR(200),
    college VARCHAR(200),
    shoots VARCHAR(10),
    official_image_src TEXT,
    social_media_accounts JSONB DEFAULT '[]',
    external_mappings JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Teams table
CREATE TABLE teams (
    id BIGINT PRIMARY KEY,
    abbreviation VARCHAR(10) NOT NULL UNIQUE,
    city VARCHAR(100) NOT NULL,
    name VARCHAR(100) NOT NULL,
    home_venue_id BIGINT,
    team_colors_hex VARCHAR(7)[],
    social_media_accounts JSONB DEFAULT '[]',
    official_logo_src TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Venues table
CREATE TABLE venues (
    id BIGINT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    city VARCHAR(100),
    country VARCHAR(50),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    capacity INTEGER,
    has_roof BOOLEAN DEFAULT FALSE,
    has_retractable_roof BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Games table
CREATE TABLE games (
    id BIGINT PRIMARY KEY,
    season VARCHAR(10) NOT NULL,
    game_date DATE NOT NULL,
    game_time TIME,
    away_team_id BIGINT NOT NULL REFERENCES teams(id),
    home_team_id BIGINT NOT NULL REFERENCES teams(id),
    venue_id BIGINT REFERENCES venues(id),
    game_status game_status DEFAULT 'SCHEDULED',
    away_score INTEGER,
    home_score INTEGER,
    quarters JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Player injuries table
CREATE TABLE player_injuries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    player_id BIGINT NOT NULL REFERENCES players(id),
    injury_description VARCHAR(200),
    playing_probability injury_status,
    injury_date DATE,
    expected_return_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Player game logs table
CREATE TABLE player_game_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    player_id BIGINT NOT NULL REFERENCES players(id),
    game_id BIGINT NOT NULL REFERENCES games(id),
    team_id BIGINT NOT NULL REFERENCES teams(id),
    minutes_played INTEGER,
    field_goals_made INTEGER DEFAULT 0,
    field_goals_attempted INTEGER DEFAULT 0,
    three_pointers_made INTEGER DEFAULT 0,
    three_pointers_attempted INTEGER DEFAULT 0,
    free_throws_made INTEGER DEFAULT 0,
    free_throws_attempted INTEGER DEFAULT 0,
    rebounds INTEGER DEFAULT 0,
    assists INTEGER DEFAULT 0,
    steals INTEGER DEFAULT 0,
    blocks INTEGER DEFAULT 0,
    turnovers INTEGER DEFAULT 0,
    personal_fouls INTEGER DEFAULT 0,
    points INTEGER DEFAULT 0,
    plus_minus INTEGER DEFAULT 0,
    fantasy_points DECIMAL(10, 2) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(player_id, game_id)
);

-- DFS projections table
CREATE TABLE dfs_projections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    player_id BIGINT NOT NULL REFERENCES players(id),
    game_id BIGINT NOT NULL REFERENCES games(id),
    projection_date DATE NOT NULL,
    source VARCHAR(50) NOT NULL,
    salary DECIMAL(10, 2),
    projected_points DECIMAL(10, 2),
    projected_value DECIMAL(10, 4),
    ownership_percentage DECIMAL(5, 2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(player_id, game_id, projection_date, source)
);

-- Daily DFS data table
CREATE TABLE daily_dfs_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    player_id BIGINT NOT NULL REFERENCES players(id),
    game_id BIGINT NOT NULL REFERENCES games(id),
    dfs_date DATE NOT NULL,
    source VARCHAR(50) NOT NULL,
    salary DECIMAL(10, 2),
    actual_points DECIMAL(10, 2),
    value DECIMAL(10, 4),
    ownership_percentage DECIMAL(5, 2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(player_id, game_id, dfs_date, source)
);

-- Game lineups table
CREATE TABLE game_lineups (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    game_id BIGINT NOT NULL REFERENCES games(id),
    team_id BIGINT NOT NULL REFERENCES teams(id),
    player_id BIGINT NOT NULL REFERENCES players(id),
    position VARCHAR(10),
    starter BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(game_id, team_id, player_id)
);

-- Data sync tracking table
CREATE TABLE data_sync_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sync_type VARCHAR(50) NOT NULL,
    sync_date DATE NOT NULL,
    records_processed INTEGER DEFAULT 0,
    records_created INTEGER DEFAULT 0,
    records_updated INTEGER DEFAULT 0,
    records_skipped INTEGER DEFAULT 0,
    sync_duration_ms INTEGER,
    status VARCHAR(20) NOT NULL, -- 'SUCCESS', 'FAILED', 'PARTIAL'
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX idx_players_team ON players(current_team_id);
CREATE INDEX idx_players_position ON players(primary_position);
CREATE INDEX idx_players_name ON players(first_name, last_name);
CREATE INDEX idx_games_date ON games(game_date);
CREATE INDEX idx_games_season ON games(season);
CREATE INDEX idx_games_teams ON games(away_team_id, home_team_id);
CREATE INDEX idx_player_game_logs_player ON player_game_logs(player_id);
CREATE INDEX idx_player_game_logs_game ON player_game_logs(game_id);
CREATE INDEX idx_player_game_logs_date ON player_game_logs(created_at);
CREATE INDEX idx_dfs_projections_player ON dfs_projections(player_id);
CREATE INDEX idx_dfs_projections_date ON dfs_projections(projection_date);
CREATE INDEX idx_daily_dfs_data_player ON daily_dfs_data(player_id);
CREATE INDEX idx_daily_dfs_data_date ON daily_dfs_data(dfs_date);
CREATE INDEX idx_player_injuries_player ON player_injuries(player_id);
CREATE INDEX idx_game_lineups_game ON game_lineups(game_id);
CREATE INDEX idx_game_lineups_team ON game_lineups(team_id);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at triggers to all tables
CREATE TRIGGER update_players_updated_at BEFORE UPDATE ON players FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_teams_updated_at BEFORE UPDATE ON teams FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_venues_updated_at BEFORE UPDATE ON venues FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_games_updated_at BEFORE UPDATE ON games FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_player_injuries_updated_at BEFORE UPDATE ON player_injuries FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_player_game_logs_updated_at BEFORE UPDATE ON player_game_logs FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_dfs_projections_updated_at BEFORE UPDATE ON dfs_projections FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_daily_dfs_data_updated_at BEFORE UPDATE ON daily_dfs_data FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_game_lineups_updated_at BEFORE UPDATE ON game_lineups FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create views for common queries
CREATE VIEW active_players AS
SELECT p.*, t.abbreviation as team_abbreviation, t.city as team_city, t.name as team_name
FROM players p
LEFT JOIN teams t ON p.current_team_id = t.id
WHERE p.current_roster_status = 'ROSTER';

CREATE VIEW upcoming_games AS
SELECT g.*, 
       at.abbreviation as away_team_abbreviation, at.city as away_team_city, at.name as away_team_name,
       ht.abbreviation as home_team_abbreviation, ht.city as home_team_city, ht.name as home_team_name,
       v.name as venue_name, v.city as venue_city
FROM games g
LEFT JOIN teams at ON g.away_team_id = at.id
LEFT JOIN teams ht ON g.home_team_id = ht.id
LEFT JOIN venues v ON g.venue_id = v.id
WHERE g.game_status IN ('SCHEDULED', 'IN_PROGRESS')
ORDER BY g.game_date, g.game_time;

CREATE VIEW injured_players AS
SELECT p.*, pi.injury_description, pi.playing_probability, pi.injury_date, pi.expected_return_date,
       t.abbreviation as team_abbreviation, t.city as team_city, t.name as team_name
FROM players p
JOIN player_injuries pi ON p.id = pi.player_id
LEFT JOIN teams t ON p.current_team_id = t.id
WHERE pi.playing_probability IN ('OUT', 'QUESTIONABLE', 'DOUBTFUL')
ORDER BY pi.playing_probability, p.last_name, p.first_name;

-- Grant necessary permissions (adjust as needed for your setup)
-- GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
-- GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO authenticated;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO authenticated;
