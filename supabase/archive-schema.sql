-- NBA Fantasy Optimizer Archive Schema
-- This file contains archive tables for historical data management

-- Archive tables for annual data (players, teams, games)
-- These tables store complete historical records with season_year and archived_at

-- Archive Players table
CREATE TABLE archive_players (
    id BIGINT,
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
    season_year INTEGER NOT NULL, -- The season this data applies to
    archived_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(), -- When this record was archived
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (id, season_year)
);

-- Archive Teams table
CREATE TABLE archive_teams (
    id BIGINT,
    abbreviation VARCHAR(10) NOT NULL,
    city VARCHAR(100) NOT NULL,
    name VARCHAR(100) NOT NULL,
    home_venue_id BIGINT,
    team_colors_hex VARCHAR(7)[],
    social_media_accounts JSONB DEFAULT '[]',
    official_logo_src TEXT,
    season_year INTEGER NOT NULL, -- The season this data applies to
    archived_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(), -- When this record was archived
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (id, season_year)
);

-- Archive Games table
CREATE TABLE archive_games (
    id BIGINT,
    season VARCHAR(10) NOT NULL,
    game_date DATE NOT NULL,
    game_time TIME,
    away_team_id BIGINT NOT NULL,
    home_team_id BIGINT NOT NULL,
    venue_id BIGINT,
    game_status game_status DEFAULT 'SCHEDULED',
    away_score INTEGER DEFAULT 0,
    home_score INTEGER DEFAULT 0,
    attendance INTEGER,
    officials JSONB DEFAULT '[]',
    broadcasters VARCHAR(100)[],
    weather_data JSONB,
    season_year INTEGER NOT NULL, -- The season this data applies to
    archived_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(), -- When this record was archived
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (id, season_year)
);

-- Archive tables for rolling data (stats, injuries, DFS data)
-- These tables keep current + previous year data, archive older data

-- Archive Player Game Logs table
CREATE TABLE archive_player_game_logs (
    id BIGSERIAL PRIMARY KEY,
    player_id BIGINT NOT NULL,
    game_id BIGINT NOT NULL,
    team_id BIGINT NOT NULL,
    game_date DATE NOT NULL,
    stats JSONB DEFAULT '{}',
    season_year INTEGER NOT NULL, -- The season this data applies to
    archived_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(), -- When this record was archived
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Archive Player Injuries table
CREATE TABLE archive_player_injuries (
    id BIGSERIAL PRIMARY KEY,
    player_id BIGINT NOT NULL,
    team_id BIGINT,
    injury_type VARCHAR(100),
    injury_status injury_status,
    description TEXT,
    playing_probability VARCHAR(20),
    injury_date DATE,
    expected_return_date DATE,
    season_year INTEGER NOT NULL, -- The season this data applies to
    archived_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(), -- When this record was archived
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Archive DFS Projections table
CREATE TABLE archive_dfs_projections (
    id BIGSERIAL PRIMARY KEY,
    player_id BIGINT NOT NULL,
    team_id BIGINT NOT NULL,
    game_id BIGINT NOT NULL,
    projection_date DATE NOT NULL,
    fantasy_points JSONB DEFAULT '{}',
    salary DECIMAL(10,2),
    ownership_percentage DECIMAL(5,2),
    season_year INTEGER NOT NULL, -- The season this data applies to
    archived_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(), -- When this record was archived
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Archive Daily DFS Data table
CREATE TABLE archive_daily_dfs_data (
    id BIGSERIAL PRIMARY KEY,
    player_id BIGINT NOT NULL,
    team_id BIGINT NOT NULL,
    game_id BIGINT NOT NULL,
    data_date DATE NOT NULL,
    fantasy_points JSONB DEFAULT '{}',
    salary DECIMAL(10,2),
    ownership_percentage DECIMAL(5,2),
    season_year INTEGER NOT NULL, -- The season this data applies to
    archived_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(), -- When this record was archived
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for archive tables for better performance
CREATE INDEX idx_archive_players_season_year ON archive_players(season_year);
CREATE INDEX idx_archive_players_archived_at ON archive_players(archived_at);
CREATE INDEX idx_archive_players_team_id ON archive_players(current_team_id);

CREATE INDEX idx_archive_teams_season_year ON archive_teams(season_year);
CREATE INDEX idx_archive_teams_archived_at ON archive_teams(archived_at);

CREATE INDEX idx_archive_games_season_year ON archive_games(season_year);
CREATE INDEX idx_archive_games_archived_at ON archive_games(archived_at);
CREATE INDEX idx_archive_games_date ON archive_games(game_date);
CREATE INDEX idx_archive_games_teams ON archive_games(away_team_id, home_team_id);

CREATE INDEX idx_archive_player_game_logs_season_year ON archive_player_game_logs(season_year);
CREATE INDEX idx_archive_player_game_logs_archived_at ON archive_player_game_logs(archived_at);
CREATE INDEX idx_archive_player_game_logs_player_id ON archive_player_game_logs(player_id);
CREATE INDEX idx_archive_player_game_logs_game_id ON archive_player_game_logs(game_id);

CREATE INDEX idx_archive_player_injuries_season_year ON archive_player_injuries(season_year);
CREATE INDEX idx_archive_player_injuries_archived_at ON archive_player_injuries(archived_at);
CREATE INDEX idx_archive_player_injuries_player_id ON archive_player_injuries(player_id);

CREATE INDEX idx_archive_dfs_projections_season_year ON archive_dfs_projections(season_year);
CREATE INDEX idx_archive_dfs_projections_archived_at ON archive_dfs_projections(archived_at);
CREATE INDEX idx_archive_dfs_projections_player_id ON archive_dfs_projections(player_id);
CREATE INDEX idx_archive_dfs_projections_date ON archive_dfs_projections(projection_date);

CREATE INDEX idx_archive_daily_dfs_data_season_year ON archive_daily_dfs_data(season_year);
CREATE INDEX idx_archive_daily_dfs_data_archived_at ON archive_daily_dfs_data(archived_at);
CREATE INDEX idx_archive_daily_dfs_data_player_id ON archive_daily_dfs_data(player_id);
CREATE INDEX idx_archive_daily_dfs_data_date ON archive_daily_dfs_data(data_date);

-- Create views for ML/AI access to current and archived data
-- These views combine current and archived data for seamless access

-- View for all players (current + archived)
CREATE VIEW v_all_players AS
SELECT 
    id,
    first_name,
    last_name,
    primary_position,
    alternate_positions,
    jersey_number,
    current_team_id,
    current_roster_status,
    height,
    weight,
    birth_date,
    age,
    birth_city,
    birth_country,
    rookie,
    high_school,
    college,
    shoots,
    official_image_src,
    social_media_accounts,
    external_mappings,
    season_year,
    archived_at,
    created_at,
    updated_at,
    'current' as data_source
FROM players
UNION ALL
SELECT 
    id,
    first_name,
    last_name,
    primary_position,
    alternate_positions,
    jersey_number,
    current_team_id,
    current_roster_status,
    height,
    weight,
    birth_date,
    age,
    birth_city,
    birth_country,
    rookie,
    high_school,
    college,
    shoots,
    official_image_src,
    social_media_accounts,
    external_mappings,
    season_year,
    archived_at,
    created_at,
    updated_at,
    'archived' as data_source
FROM archive_players;

-- View for all teams (current + archived)
CREATE VIEW v_all_teams AS
SELECT 
    id,
    abbreviation,
    city,
    name,
    home_venue_id,
    team_colors_hex,
    social_media_accounts,
    official_logo_src,
    season_year,
    archived_at,
    created_at,
    updated_at,
    'current' as data_source
FROM teams
UNION ALL
SELECT 
    id,
    abbreviation,
    city,
    name,
    home_venue_id,
    team_colors_hex,
    social_media_accounts,
    official_logo_src,
    season_year,
    archived_at,
    created_at,
    updated_at,
    'archived' as data_source
FROM archive_teams;

-- View for all games (current + archived)
CREATE VIEW v_all_games AS
SELECT 
    id,
    season,
    game_date,
    game_time,
    away_team_id,
    home_team_id,
    venue_id,
    game_status,
    away_score,
    home_score,
    attendance,
    officials,
    broadcasters,
    weather_data,
    season_year,
    archived_at,
    created_at,
    updated_at,
    'current' as data_source
FROM games
UNION ALL
SELECT 
    id,
    season,
    game_date,
    game_time,
    away_team_id,
    home_team_id,
    venue_id,
    game_status,
    away_score,
    home_score,
    attendance,
    officials,
    broadcasters,
    weather_data,
    season_year,
    archived_at,
    created_at,
    updated_at,
    'archived' as data_source
FROM archive_games;

-- View for all player game logs (current + archived)
CREATE VIEW v_all_player_game_logs AS
SELECT 
    id,
    player_id,
    game_id,
    team_id,
    game_date,
    stats,
    season_year,
    archived_at,
    created_at,
    updated_at,
    'current' as data_source
FROM player_game_logs
UNION ALL
SELECT 
    id,
    player_id,
    game_id,
    team_id,
    game_date,
    stats,
    season_year,
    archived_at,
    created_at,
    updated_at,
    'archived' as data_source
FROM archive_player_game_logs;

-- View for all player injuries (current + archived)
CREATE VIEW v_all_player_injuries AS
SELECT 
    id,
    player_id,
    team_id,
    injury_type,
    injury_status,
    description,
    playing_probability,
    injury_date,
    expected_return_date,
    season_year,
    archived_at,
    created_at,
    updated_at,
    'current' as data_source
FROM player_injuries
UNION ALL
SELECT 
    id,
    player_id,
    team_id,
    injury_type,
    injury_status,
    description,
    playing_probability,
    injury_date,
    expected_return_date,
    season_year,
    archived_at,
    created_at,
    updated_at,
    'archived' as data_source
FROM archive_player_injuries;

-- View for all DFS projections (current + archived)
CREATE VIEW v_all_dfs_projections AS
SELECT 
    id,
    player_id,
    team_id,
    game_id,
    projection_date,
    fantasy_points,
    salary,
    ownership_percentage,
    season_year,
    archived_at,
    created_at,
    updated_at,
    'current' as data_source
FROM dfs_projections
UNION ALL
SELECT 
    id,
    player_id,
    team_id,
    game_id,
    projection_date,
    fantasy_points,
    salary,
    ownership_percentage,
    season_year,
    archived_at,
    created_at,
    updated_at,
    'archived' as data_source
FROM archive_dfs_projections;

-- View for all daily DFS data (current + archived)
CREATE VIEW v_all_daily_dfs_data AS
SELECT 
    id,
    player_id,
    team_id,
    game_id,
    data_date,
    fantasy_points,
    salary,
    ownership_percentage,
    season_year,
    archived_at,
    created_at,
    updated_at,
    'current' as data_source
FROM daily_dfs_data
UNION ALL
SELECT 
    id,
    player_id,
    team_id,
    game_id,
    data_date,
    fantasy_points,
    salary,
    ownership_percentage,
    season_year,
    archived_at,
    created_at,
    updated_at,
    'archived' as data_source
FROM archive_daily_dfs_data;

