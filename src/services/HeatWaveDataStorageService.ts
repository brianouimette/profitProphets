import { heatwaveService } from './HeatWaveClient';
import { logger } from '../utils/logger';

export interface PlayerData {
    id: number;
    first_name: string;
    last_name: string;
    primary_position: string;
    alternate_positions?: string[];
    jersey_number?: string | number | null;
    current_team_id?: number | null;
    current_roster_status?: string;
    height?: string | null;
    weight?: number | null;
    birth_date?: string | null;
    age?: number | null;
    birth_city?: string | null;
    birth_country?: string | null;
    rookie?: boolean;
    high_school?: string | null;
    college?: string | null;
    shoots?: string | null;
    official_image_src?: string | null;
    social_media_accounts?: any[];
    external_mappings?: any[];
}

export interface TeamData {
    id: number;
    abbreviation: string;
    city?: string;
    name?: string;
    conference?: string;
    division?: string;
}

export interface GameData {
    id: number;
    game_date: string | null;
    away_team_id: number | null;
    home_team_id: number | null;
    status?: string | null;
    away_score?: number | null;
    home_score?: number | null;
    season?: string | null;
    game_type?: string;
}

export interface InjuryData {
    id: number;
    player_id: number;
    injury_type?: string;
    status?: string;
    start_date?: string | null;
    expected_return?: string | null;
    description?: string;
}

export interface GameLogData {
    id?: number; // Auto-increment, optional for inserts
    player_id: number;
    game_id: number;
    minutes_played?: number;
    rebounds?: number;
    assists?: number;
    steals?: number;
    blocks?: number;
    turnovers?: number;
    field_goals_made?: number;
    field_goals_attempted?: number;
    three_pointers_made?: number;
    three_pointers_attempted?: number;
    free_throws_made?: number;
    free_throws_attempted?: number;
    personal_fouls?: number;
    plus_minus?: number;
    fantasy_points?: number;
}

export interface DfsProjectionData {
    id?: number; // Auto-increment, optional for inserts
    player_id: number;
    game_id: number;
    salary?: number | null;
    projected_fantasy_points?: number | null;
    ownership_percentage?: number | null;
    ceiling?: number | null;
    floor?: number | null;
    value_score?: number | null;
}

export interface DailyDfsData {
    id?: number; // Auto-increment, optional for inserts
    player_id: number;
    game_id: number;
    fantasy_points?: number | null;
    salary?: number | null;
    ownership_percentage?: number | null;
    slate_id?: string | null;
    platform?: string | null;
}

export interface SyncLogData {
    table_name: string;
    sync_date: string;
    records_processed: number;
    records_created: number;
    records_updated: number;
    records_errors: number;
    duration_ms: number;
    status: string;
}

class HeatWaveDataStorageService {
    /**
     * Store players data with upsert logic
     */
    async storePlayers(players: PlayerData[]): Promise<{ created: number; updated: number; errors: number }> {
        if (!(await this._check_connection())) {
            return { created: 0, updated: 0, errors: players.length };
        }

        let created = 0;
        let updated = 0;
        let errors = 0;

        for (const player of players) {
            try {
                // Check if player exists
                const existing = await heatwaveService.queryOne(
                    'SELECT id FROM players WHERE id = ?',
                    [player.id]
                );

                if (existing) {
                    // Update existing player
                    await heatwaveService.query(
                        `UPDATE players SET 
                         first_name = ?, last_name = ?, primary_position = ?, 
                         alternate_positions = ?, jersey_number = ?, current_team_id = ?,
                         current_roster_status = ?, height = ?, weight = ?, 
                         birth_date = ?, age = ?, birth_city = ?, birth_country = ?,
                         rookie = ?, high_school = ?, college = ?, shoots = ?,
                         official_image_src = ?, social_media_accounts = ?, 
                         external_mappings = ?, updated_at = NOW()
                         WHERE id = ?`,
                        [
                            player.first_name, player.last_name, player.primary_position,
                            JSON.stringify(player.alternate_positions || []),
                            player.jersey_number, player.current_team_id,
                            player.current_roster_status, player.height, player.weight,
                            player.birth_date, player.age, player.birth_city, player.birth_country,
                            player.rookie, player.high_school, player.college, player.shoots,
                            player.official_image_src,
                            JSON.stringify(player.social_media_accounts || []),
                            JSON.stringify(player.external_mappings || []),
                            player.id
                        ]
                    );
                    updated++;
                } else {
                    // Insert new player
                    await heatwaveService.query(
                        `INSERT INTO players (
                            id, first_name, last_name, primary_position, alternate_positions,
                            jersey_number, current_team_id, current_roster_status, height, weight,
                            birth_date, age, birth_city, birth_country, rookie, high_school,
                            college, shoots, official_image_src, social_media_accounts,
                            external_mappings, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NOW(), NOW())`,
                        [
                            player.id, player.first_name, player.last_name, player.primary_position,
                            JSON.stringify(player.alternate_positions || []),
                            player.jersey_number, player.current_team_id,
                            player.current_roster_status, player.height, player.weight,
                            player.birth_date, player.age, player.birth_city, player.birth_country,
                            player.rookie, player.high_school, player.college, player.shoots,
                            player.official_image_src,
                            JSON.stringify(player.social_media_accounts || []),
                            JSON.stringify(player.external_mappings || [])
                        ]
                    );
                    created++;
                }
            } catch (error) {
                logger.error(`Error storing player ${player.id}:`, error);
                errors++;
            }
        }

        return { created, updated, errors };
    }

    /**
     * Store teams data with upsert logic
     */
    async storeTeams(teams: TeamData[]): Promise<{ created: number; updated: number; errors: number }> {
        if (!(await this._check_connection())) {
            return { created: 0, updated: 0, errors: teams.length };
        }

        let created = 0;
        let updated = 0;
        let errors = 0;

        for (const team of teams) {
            try {
                // Check if team exists
                const existing = await heatwaveService.queryOne(
                    'SELECT id FROM teams WHERE id = ?',
                    [team.id]
                );

                if (existing) {
                    // Update existing team
                    await heatwaveService.query(
                        `UPDATE teams SET 
                         abbreviation = ?, city = ?, name = ?, 
                         conference = ?, division = ?, updated_at = NOW()
                         WHERE id = ?`,
                        [team.abbreviation, team.city, team.name, team.conference, team.division, team.id]
                    );
                    updated++;
                } else {
                    // Insert new team
                    await heatwaveService.query(
                        `INSERT INTO teams (id, abbreviation, city, name, conference, division, created_at, updated_at) 
                         VALUES (?, ?, ?, ?, ?, ?, NOW(), NOW())`,
                        [team.id, team.abbreviation, team.city, team.name, team.conference, team.division]
                    );
                    created++;
                }
            } catch (error) {
                logger.error(`Error storing team ${team.id}:`, error);
                errors++;
            }
        }

        return { created, updated, errors };
    }

    /**
     * Store games data with upsert logic
     */
    async storeGames(games: GameData[]): Promise<{ created: number; updated: number; errors: number }> {
        if (!(await this._check_connection())) {
            return { created: 0, updated: 0, errors: games.length };
        }

        let created = 0;
        let updated = 0;
        let errors = 0;

        for (const game of games) {
            try {
                // Skip games without valid IDs
                if (!game.id || game.id === undefined || game.id === null) {
                    logger.warn(`Skipping game with invalid ID: ${JSON.stringify(game)}`);
                    errors++;
                    continue;
                }

                // Check if game exists
                const existing = await heatwaveService.queryOne(
                    'SELECT id FROM games WHERE id = ?',
                    [game.id]
                );

                if (existing) {
                    // Update existing game - convert undefined to null for SQL
                    await heatwaveService.query(
                        `UPDATE games SET 
                         game_date = ?, home_team_id = ?, away_team_id = ?, 
                         home_score = ?, away_score = ?, status = ?, season = ?, game_type = ?, updated_at = NOW()
                         WHERE id = ?`,
                        [
                            game.game_date || null,
                            game.home_team_id ?? null,
                            game.away_team_id ?? null,
                            game.home_score ?? null,
                            game.away_score ?? null,
                            game.status || null,
                            game.season || null,
                            game.game_type || 'REGULAR',
                            game.id
                        ]
                    );
                    updated++;
                } else {
                    // Insert new game - convert undefined to null for SQL
                    // Column order: id, game_date, home_team_id, away_team_id, home_score, away_score, status, season, game_type
                    await heatwaveService.query(
                        `INSERT INTO games (id, game_date, home_team_id, away_team_id, home_score, away_score, status, season, game_type, created_at, updated_at) 
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NOW(), NOW())`,
                        [
                            game.id,
                            game.game_date || null,
                            game.home_team_id ?? null,
                            game.away_team_id ?? null,
                            game.home_score ?? null,
                            game.away_score ?? null,
                            game.status || null,
                            game.season || null,
                            game.game_type || 'REGULAR'
                        ]
                    );
                    created++;
                }
            } catch (error) {
                logger.error(`Error storing game ${game.id}:`, error);
                errors++;
            }
        }

        return { created, updated, errors };
    }

    /**
     * Store injuries data with upsert logic
     */
    async storeInjuries(injuries: InjuryData[]): Promise<{ created: number; updated: number; errors: number }> {
        if (!(await this._check_connection())) {
            return { created: 0, updated: 0, errors: injuries.length };
        }

        let created = 0;
        let updated = 0;
        let errors = 0;

        for (const injury of injuries) {
            try {
                // Check if injury exists
                const existing = await heatwaveService.queryOne(
                    'SELECT id FROM injuries WHERE id = ?',
                    [injury.id]
                );

                if (existing) {
                    // Update existing injury
                    await heatwaveService.query(
                        `UPDATE injuries SET 
                         player_id = ?, injury_type = ?, status = ?, 
                         start_date = ?, expected_return = ?, description = ?, updated_at = NOW()
                         WHERE id = ?`,
                        [
                            injury.player_id,
                            injury.injury_type,
                            injury.status,
                            injury.start_date ?? null,
                            injury.expected_return ?? null,
                            injury.description,
                            injury.id
                        ]
                    );
                    updated++;
                } else {
                    // Insert new injury
                    await heatwaveService.query(
                        `INSERT INTO injuries (id, player_id, injury_type, status, start_date, expected_return, description, created_at, updated_at) 
                         VALUES (?, ?, ?, ?, ?, ?, ?, NOW(), NOW())`,
                        [
                            injury.id,
                            injury.player_id,
                            injury.injury_type,
                            injury.status,
                            injury.start_date ?? null,
                            injury.expected_return ?? null,
                            injury.description
                        ]
                    );
                    created++;
                }
            } catch (error) {
                logger.error(`Error storing injury ${injury.id}:`, error);
                errors++;
            }
        }

        return { created, updated, errors };
    }

    /**
     * Store game logs data with upsert logic
     */
    async storeGameLogs(gameLogs: GameLogData[]): Promise<{ created: number; updated: number; errors: number }> {
        if (!(await this._check_connection())) {
            return { created: 0, updated: 0, errors: gameLogs.length };
        }

        let created = 0;
        let updated = 0;
        let errors = 0;

        for (const log of gameLogs) {
            try {
                // Check if game log exists using player_id and game_id (since id is auto-increment)
                const existing = await heatwaveService.queryOne(
                    'SELECT id FROM player_game_logs WHERE player_id = ? AND game_id = ?',
                    [log.player_id, log.game_id]
                );

                if (existing) {
                    // Update existing game log - removed team_id and opponent_team_id (not in schema)
                    await heatwaveService.query(
                        `UPDATE player_game_logs SET 
                         minutes_played = ?, field_goals_made = ?, field_goals_attempted = ?,
                         three_pointers_made = ?, three_pointers_attempted = ?, free_throws_made = ?,
                         free_throws_attempted = ?, rebounds = ?, assists = ?, steals = ?,
                         blocks = ?, turnovers = ?, personal_fouls = ?, plus_minus = ?, fantasy_points = ?
                         WHERE player_id = ? AND game_id = ?`,
                        [
                            log.minutes_played ?? null, log.field_goals_made ?? null, log.field_goals_attempted ?? null,
                            log.three_pointers_made ?? null, log.three_pointers_attempted ?? null, log.free_throws_made ?? null,
                            log.free_throws_attempted ?? null, log.rebounds ?? null, log.assists ?? null, log.steals ?? null,
                            log.blocks ?? null, log.turnovers ?? null, log.personal_fouls ?? null, log.plus_minus ?? null, log.fantasy_points ?? null,
                            log.player_id, log.game_id
                        ]
                    );
                    updated++;
                } else {
                    // Insert new game log - removed team_id and opponent_team_id (not in schema)
                    // id is auto-increment, so not included
                    await heatwaveService.query(
                        `INSERT INTO player_game_logs (
                            player_id, game_id, fantasy_points, minutes_played,
                            field_goals_made, field_goals_attempted, three_pointers_made,
                            three_pointers_attempted, free_throws_made, free_throws_attempted,
                            rebounds, assists, steals, blocks, turnovers, personal_fouls, plus_minus,
                            created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NOW())`,
                        [
                            log.player_id, log.game_id, log.fantasy_points ?? null, log.minutes_played ?? null,
                            log.field_goals_made ?? null, log.field_goals_attempted ?? null, log.three_pointers_made ?? null,
                            log.three_pointers_attempted ?? null, log.free_throws_made ?? null, log.free_throws_attempted ?? null,
                            log.rebounds ?? null, log.assists ?? null, log.steals ?? null, log.blocks ?? null,
                            log.turnovers ?? null, log.personal_fouls ?? null, log.plus_minus ?? null
                        ]
                    );
                    created++;
                }
            } catch (error) {
                logger.error(`Error storing game log for player ${log.player_id}, game ${log.game_id}:`, error);
                errors++;
            }
        }

        return { created, updated, errors };
    }

    /**
     * Store DFS projections data with upsert logic
     */
    async storeDfsProjections(projections: DfsProjectionData[]): Promise<{ created: number; updated: number; errors: number }> {
        if (!(await this._check_connection())) {
            return { created: 0, updated: 0, errors: projections.length };
        }

        let created = 0;
        let updated = 0;
        let errors = 0;

        for (const projection of projections) {
            try {
                // Check if projection exists using player_id and game_id (since id is auto-increment)
                const existing = await heatwaveService.queryOne(
                    'SELECT id FROM dfs_projections WHERE player_id = ? AND game_id = ?',
                    [projection.player_id, projection.game_id]
                );

                if (existing) {
                    // Update existing projection - removed date column (not in schema), use projected_fantasy_points
                    await heatwaveService.query(
                        `UPDATE dfs_projections SET 
                         player_id = ?, game_id = ?, salary = ?,
                         projected_fantasy_points = ?, ownership_percentage = ?, ceiling = ?, floor = ?, value_score = ?, updated_at = NOW()
                         WHERE player_id = ? AND game_id = ?`,
                        [
                            projection.player_id, projection.game_id, projection.salary ?? null,
                            projection.projected_fantasy_points ?? null, projection.ownership_percentage ?? null,
                            projection.ceiling ?? null, projection.floor ?? null, projection.value_score ?? null,
                            projection.player_id, projection.game_id
                        ]
                    );
                    updated++;
                } else {
                    // Insert new projection - removed date column and id (auto-increment), use projected_fantasy_points
                    await heatwaveService.query(
                        `INSERT INTO dfs_projections (player_id, game_id, salary, projected_fantasy_points, ownership_percentage, ceiling, floor, value_score, created_at, updated_at) 
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, NOW(), NOW())`,
                        [
                            projection.player_id, projection.game_id, projection.salary ?? null,
                            projection.projected_fantasy_points ?? null, projection.ownership_percentage ?? null,
                            projection.ceiling ?? null, projection.floor ?? null, projection.value_score ?? null
                        ]
                    );
                    created++;
                }
            } catch (error) {
                logger.error(`Error storing DFS projection for player ${projection.player_id}, game ${projection.game_id}:`, error);
                errors++;
            }
        }

        return { created, updated, errors };
    }

    /**
     * Log sync operation
     */
    async logSyncOperation(
        tableName: string,
        syncDate: string,
        recordsProcessed: number,
        recordsCreated: number,
        recordsUpdated: number,
        recordsErrors: number,
        durationMs: number,
        status: string
    ): Promise<void> {
        try {
            await heatwaveService.query(
                `INSERT INTO data_sync_logs (
                    table_name, sync_date, records_processed, records_created, 
                    records_updated, records_errors, duration_ms, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, NOW())`,
                [tableName, syncDate, recordsProcessed, recordsCreated, recordsUpdated, recordsErrors, durationMs, status]
            );
        } catch (error) {
            logger.error('Error logging sync operation:', error);
        }
    }

    /**
     * Get active players
     */
    async getActivePlayers(): Promise<PlayerData[]> {
        if (!(await this._check_connection())) {
            return [];
        }

        try {
            const players = await heatwaveService.query<PlayerData>(
                'SELECT * FROM players WHERE current_roster_status = "ACTIVE"'
            );
            return players;
        } catch (error) {
            logger.error('Error getting active players:', error);
            return [];
        }
    }

    /**
     * Get upcoming games
     */
    async getUpcomingGames(days: number = 7): Promise<GameData[]> {
        if (!(await this._check_connection())) {
            return [];
        }

        try {
            const games = await heatwaveService.query<GameData>(
                'SELECT * FROM games WHERE date >= CURDATE() AND date <= DATE_ADD(CURDATE(), INTERVAL ? DAY) ORDER BY date',
                [days]
            );
            return games;
        } catch (error) {
            logger.error('Error getting upcoming games:', error);
            return [];
        }
    }

    /**
     * Get injured players
     */
    async getInjuredPlayers(): Promise<PlayerData[]> {
        if (!(await this._check_connection())) {
            return [];
        }

        try {
            const players = await heatwaveService.query<PlayerData>(
                `SELECT p.* FROM players p 
                 JOIN injuries i ON p.id = i.player_id 
                 WHERE i.status IN ('INJURED', 'OUT', 'QUESTIONABLE')`
            );
            return players;
        } catch (error) {
            logger.error('Error getting injured players:', error);
            return [];
        }
    }

    /**
     * Get sync history
     */
    async getSyncHistory(limit: number = 10): Promise<any[]> {
        if (!(await this._check_connection())) {
            return [];
        }

        try {
            const history = await heatwaveService.query(
                'SELECT * FROM data_sync_logs ORDER BY created_at DESC LIMIT ?',
                [limit]
            );
            return history;
        } catch (error) {
            logger.error('Error getting sync history:', error);
            return [];
        }
    }

    private async _check_connection(): Promise<boolean> {
        return await heatwaveService.testConnection();
    }
}

// Export singleton instance
export const heatwaveDataStorageService = new HeatWaveDataStorageService();
