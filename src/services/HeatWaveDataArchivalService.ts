import { heatwaveService } from './HeatWaveClient';
import { logger } from '../utils/logger';

export interface ArchivalConfig {
    // Annual archival settings
    archivePlayersAfterYears: number;
    archiveTeamsAfterYears: number;
    archiveGamesAfterYears: number;
    archiveGameLogsAfterYears: number;
    archiveInjuriesAfterYears: number;
    archiveProjectionsAfterYears: number;
    archiveDfsDataAfterYears: number;

    // Data retention settings
    keepRecentDataDays: number;
    compressionEnabled: boolean;

    // Archival schedule
    archivalSchedule: 'daily' | 'weekly' | 'monthly';
    archivalTime: string; // HH:MM format
}

export interface ArchivalStatus {
    tableName: string;
    totalRecords: number;
    oldestRecord?: Date;
    newestRecord?: Date;
}

class HeatWaveDataArchivalService {
    constructor() {
        // Configuration handled by database schema
    }

    /**
     * Archive players data for a specific season
     */
    async archivePlayers(seasonYear: number): Promise<{ archived: number; errors: number }> {
        let archived = 0;
        let errors = 0;

        try {
            // Get all players from the current season
            const players = await heatwaveService.query(
                'SELECT * FROM players WHERE created_at >= ? AND created_at < ?',
                [`${seasonYear}-10-01`, `${seasonYear + 1}-10-01`]
            );

            if (players.length === 0) {
                logger.info(`No players found for season ${seasonYear}`);
                return { archived: 0, errors: 0 };
            }

            // Prepare archive data
            const archiveData = players.map((player: any) => ({
                ...player,
                season_year: seasonYear,
                archived_at: new Date().toISOString()
            }));

            // Insert into archive table
            for (const player of archiveData) {
                try {
                    await heatwaveService.query(
                        `INSERT INTO archive_players (
                            id, first_name, last_name, primary_position, alternate_positions,
                            jersey_number, current_team_id, current_roster_status, height, weight,
                            birth_date, age, birth_city, birth_country, rookie, high_school,
                            college, shoots, official_image_src, social_media_accounts,
                            external_mappings, season_year, archived_at, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
                        [
                            player.id, player.first_name, player.last_name, player.primary_position,
                            JSON.stringify(player.alternate_positions || []),
                            player.jersey_number, player.current_team_id,
                            player.current_roster_status, player.height, player.weight,
                            player.birth_date, player.age, player.birth_city, player.birth_country,
                            player.rookie, player.high_school, player.college, player.shoots,
                            player.official_image_src,
                            JSON.stringify(player.social_media_accounts || []),
                            JSON.stringify(player.external_mappings || []),
                            player.season_year, player.archived_at, player.created_at, player.updated_at
                        ]
                    );
                    archived++;
                } catch (error) {
                    logger.error(`Error archiving player ${player.id}:`, error);
                    errors++;
                }
            }

            logger.info(`Archived ${archived} players for season ${seasonYear}`);
        } catch (error) {
            logger.error(`Error archiving players for season ${seasonYear}:`, error);
            errors++;
        }

        return { archived, errors };
    }

    /**
     * Archive teams data for a specific season
     */
    async archiveTeams(seasonYear: number): Promise<{ archived: number; errors: number }> {
        let archived = 0;
        let errors = 0;

        try {
            const teams = await heatwaveService.query(
                'SELECT * FROM teams WHERE created_at >= ? AND created_at < ?',
                [`${seasonYear}-10-01`, `${seasonYear + 1}-10-01`]
            );

            if (teams.length === 0) {
                logger.info(`No teams found for season ${seasonYear}`);
                return { archived: 0, errors: 0 };
            }

            const archiveData = teams.map((team: any) => ({
                ...team,
                season_year: seasonYear,
                archived_at: new Date().toISOString()
            }));

            for (const team of archiveData) {
                try {
                    await heatwaveService.query(
                        `INSERT INTO archive_teams (
                            id, abbreviation, city, name, conference, division, 
                            season_year, archived_at, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
                        [
                            team.id, team.abbreviation, team.city, team.name,
                            team.conference, team.division, team.season_year,
                            team.archived_at, team.created_at, team.updated_at
                        ]
                    );
                    archived++;
                } catch (error) {
                    logger.error(`Error archiving team ${team.id}:`, error);
                    errors++;
                }
            }

            logger.info(`Archived ${archived} teams for season ${seasonYear}`);
        } catch (error) {
            logger.error(`Error archiving teams for season ${seasonYear}:`, error);
            errors++;
        }

        return { archived, errors };
    }

    /**
     * Archive games data for a specific season
     */
    async archiveGames(seasonYear: number): Promise<{ archived: number; errors: number }> {
        let archived = 0;
        let errors = 0;

        try {
            const games = await heatwaveService.query(
                'SELECT * FROM games WHERE date >= ? AND date < ?',
                [`${seasonYear}-10-01`, `${seasonYear + 1}-10-01`]
            );

            if (games.length === 0) {
                logger.info(`No games found for season ${seasonYear}`);
                return { archived: 0, errors: 0 };
            }

            const archiveData = games.map((game: any) => ({
                ...game,
                season_year: seasonYear,
                archived_at: new Date().toISOString()
            }));

            for (const game of archiveData) {
                try {
                    await heatwaveService.query(
                        `INSERT INTO archive_games (
                            id, date, away_team_id, home_team_id, status, away_score, 
                            home_score, venue, attendance, season_year, archived_at, 
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
                        [
                            game.id, game.date, game.away_team_id, game.home_team_id,
                            game.status, game.away_score, game.home_score, game.venue,
                            game.attendance, game.season_year, game.archived_at,
                            game.created_at, game.updated_at
                        ]
                    );
                    archived++;
                } catch (error) {
                    logger.error(`Error archiving game ${game.id}:`, error);
                    errors++;
                }
            }

            logger.info(`Archived ${archived} games for season ${seasonYear}`);
        } catch (error) {
            logger.error(`Error archiving games for season ${seasonYear}:`, error);
            errors++;
        }

        return { archived, errors };
    }

    /**
     * Archive player game logs for a specific season
     */
    async archiveGameLogs(seasonYear: number): Promise<{ archived: number; errors: number }> {
        let archived = 0;
        let errors = 0;

        try {
            const gameLogs = await heatwaveService.query(
                `SELECT pgl.* FROM player_game_logs pgl 
                 JOIN games g ON pgl.game_id = g.id 
                 WHERE g.date >= ? AND g.date < ?`,
                [`${seasonYear}-10-01`, `${seasonYear + 1}-10-01`]
            );

            if (gameLogs.length === 0) {
                logger.info(`No game logs found for season ${seasonYear}`);
                return { archived: 0, errors: 0 };
            }

            const archiveData = gameLogs.map((log: any) => ({
                ...log,
                season_year: seasonYear,
                archived_at: new Date().toISOString()
            }));

            for (const log of archiveData) {
                try {
                    await heatwaveService.query(
                        `INSERT INTO archive_player_game_logs (
                            id, player_id, game_id, team_id, opponent_team_id,
                            minutes_played, points, rebounds, assists, steals, blocks, turnovers,
                            field_goals_made, field_goals_attempted, three_pointers_made, 
                            three_pointers_attempted, free_throws_made, free_throws_attempted,
                            fantasy_points, season_year, archived_at, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
                        [
                            log.id, log.player_id, log.game_id, log.team_id, log.opponent_team_id,
                            log.minutes_played, log.points, log.rebounds, log.assists, log.steals,
                            log.blocks, log.turnovers, log.field_goals_made, log.field_goals_attempted,
                            log.three_pointers_made, log.three_pointers_attempted, log.free_throws_made,
                            log.free_throws_attempted, log.fantasy_points, log.season_year,
                            log.archived_at, log.created_at, log.updated_at
                        ]
                    );
                    archived++;
                } catch (error) {
                    logger.error(`Error archiving game log ${log.id}:`, error);
                    errors++;
                }
            }

            logger.info(`Archived ${archived} game logs for season ${seasonYear}`);
        } catch (error) {
            logger.error(`Error archiving game logs for season ${seasonYear}:`, error);
            errors++;
        }

        return { archived, errors };
    }

    /**
     * Archive injuries data for a specific season
     */
    async archiveInjuries(seasonYear: number): Promise<{ archived: number; errors: number }> {
        let archived = 0;
        let errors = 0;

        try {
            const injuries = await heatwaveService.query(
                'SELECT * FROM injuries WHERE date >= ? AND date < ?',
                [`${seasonYear}-10-01`, `${seasonYear + 1}-10-01`]
            );

            if (injuries.length === 0) {
                logger.info(`No injuries found for season ${seasonYear}`);
                return { archived: 0, errors: 0 };
            }

            const archiveData = injuries.map((injury: any) => ({
                ...injury,
                season_year: seasonYear,
                archived_at: new Date().toISOString()
            }));

            for (const injury of archiveData) {
                try {
                    await heatwaveService.query(
                        `INSERT INTO archive_injuries (
                            id, player_id, injury_type, status, date, description,
                            season_year, archived_at, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
                        [
                            injury.id, injury.player_id, injury.injury_type, injury.status,
                            injury.date, injury.description, injury.season_year,
                            injury.archived_at, injury.created_at, injury.updated_at
                        ]
                    );
                    archived++;
                } catch (error) {
                    logger.error(`Error archiving injury ${injury.id}:`, error);
                    errors++;
                }
            }

            logger.info(`Archived ${archived} injuries for season ${seasonYear}`);
        } catch (error) {
            logger.error(`Error archiving injuries for season ${seasonYear}:`, error);
            errors++;
        }

        return { archived, errors };
    }

    /**
     * Archive DFS projections for a specific season
     */
    async archiveDfsProjections(seasonYear: number): Promise<{ archived: number; errors: number }> {
        let archived = 0;
        let errors = 0;

        try {
            const projections = await heatwaveService.query(
                'SELECT * FROM dfs_projections WHERE date >= ? AND date < ?',
                [`${seasonYear}-10-01`, `${seasonYear + 1}-10-01`]
            );

            if (projections.length === 0) {
                logger.info(`No DFS projections found for season ${seasonYear}`);
                return { archived: 0, errors: 0 };
            }

            const archiveData = projections.map((projection: any) => ({
                ...projection,
                season_year: seasonYear,
                archived_at: new Date().toISOString()
            }));

            for (const projection of archiveData) {
                try {
                    await heatwaveService.query(
                        `INSERT INTO archive_dfs_projections (
                            id, player_id, game_id, date, salary, projected_points, 
                            ownership_percentage, value, season_year, archived_at, 
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
                        [
                            projection.id, projection.player_id, projection.game_id, projection.date,
                            projection.salary, projection.projected_points, projection.ownership_percentage,
                            projection.value, projection.season_year, projection.archived_at,
                            projection.created_at, projection.updated_at
                        ]
                    );
                    archived++;
                } catch (error) {
                    logger.error(`Error archiving DFS projection ${projection.id}:`, error);
                    errors++;
                }
            }

            logger.info(`Archived ${archived} DFS projections for season ${seasonYear}`);
        } catch (error) {
            logger.error(`Error archiving DFS projections for season ${seasonYear}:`, error);
            errors++;
        }

        return { archived, errors };
    }

    /**
     * Archive daily DFS data for a specific season
     */
    async archiveDailyDfsData(seasonYear: number): Promise<{ archived: number; errors: number }> {
        let archived = 0;
        let errors = 0;

        try {
            const dfsData = await heatwaveService.query(
                'SELECT * FROM daily_dfs_data WHERE date >= ? AND date < ?',
                [`${seasonYear}-10-01`, `${seasonYear + 1}-10-01`]
            );

            if (dfsData.length === 0) {
                logger.info(`No daily DFS data found for season ${seasonYear}`);
                return { archived: 0, errors: 0 };
            }

            const archiveData = dfsData.map((data: any) => ({
                ...data,
                season_year: seasonYear,
                archived_at: new Date().toISOString()
            }));

            for (const data of archiveData) {
                try {
                    await heatwaveService.query(
                        `INSERT INTO archive_daily_dfs_data (
                            id, player_id, game_id, date, salary, projected_points, 
                            ownership_percentage, value, season_year, archived_at, 
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
                        [
                            data.id, data.player_id, data.game_id, data.date,
                            data.salary, data.projected_points, data.ownership_percentage,
                            data.value, data.season_year, data.archived_at,
                            data.created_at, data.updated_at
                        ]
                    );
                    archived++;
                } catch (error) {
                    logger.error(`Error archiving daily DFS data ${data.id}:`, error);
                    errors++;
                }
            }

            logger.info(`Archived ${archived} daily DFS data for season ${seasonYear}`);
        } catch (error) {
            logger.error(`Error archiving daily DFS data for season ${seasonYear}:`, error);
            errors++;
        }

        return { archived, errors };
    }

    /**
     * Get archival status for all tables
     */
    async getArchivalStatus(): Promise<ArchivalStatus[]> {
        const results: ArchivalStatus[] = [];
        const tables = [
            'players', 'teams', 'games', 'player_game_logs',
            'injuries', 'dfs_projections', 'daily_dfs_data'
        ];

        for (const tableName of tables) {
            try {
                const countResult = await heatwaveService.queryOne(
                    `SELECT COUNT(*) as count FROM ${tableName}`
                );

                const dateResult = await heatwaveService.queryOne(
                    `SELECT MIN(created_at) as oldest, MAX(created_at) as newest FROM ${tableName}`
                );

                results.push({
                    tableName,
                    totalRecords: countResult?.count || 0,
                    oldestRecord: dateResult?.oldest ? new Date(dateResult.oldest) : undefined,
                    newestRecord: dateResult?.newest ? new Date(dateResult.newest) : undefined
                } as ArchivalStatus);
            } catch (error) {
                logger.error(`Error getting archival status for ${tableName}:`, error);
                results.push({
                    tableName,
                    totalRecords: 0
                });
            }
        }

        return results;
    }

    /**
     * Archive all data for a specific season
     */
    async archiveSeason(seasonYear: number): Promise<{
        players: { archived: number; errors: number };
        teams: { archived: number; errors: number };
        games: { archived: number; errors: number };
        gameLogs: { archived: number; errors: number };
        injuries: { archived: number; errors: number };
        projections: { archived: number; errors: number };
        dfsData: { archived: number; errors: number };
    }> {
        logger.info(`Starting archival for season ${seasonYear}`);

        const results = {
            players: await this.archivePlayers(seasonYear),
            teams: await this.archiveTeams(seasonYear),
            games: await this.archiveGames(seasonYear),
            gameLogs: await this.archiveGameLogs(seasonYear),
            injuries: await this.archiveInjuries(seasonYear),
            projections: await this.archiveDfsProjections(seasonYear),
            dfsData: await this.archiveDailyDfsData(seasonYear)
        };

        const totalArchived = Object.values(results).reduce((sum, result) => sum + result.archived, 0);
        const totalErrors = Object.values(results).reduce((sum, result) => sum + result.errors, 0);

        logger.info(`Season ${seasonYear} archival completed: ${totalArchived} records archived, ${totalErrors} errors`);

        return results;
    }
}

// Export singleton instance
export const heatwaveDataArchivalService = new HeatWaveDataArchivalService();
