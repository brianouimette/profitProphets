#!/usr/bin/env ts-node
/**
 * Fetch and Import Current Season Data
 * Fetches data from MySportsFeeds API for the current season (starting Oct 21, 2025)
 * and stores it in Oracle Cloud MySQL HeatWave database
 */

import dotenv from 'dotenv';
import { resolve } from 'path';

// Load environment variables from env.test first, then .env (BEFORE importing config)
const projectRoot = resolve(__dirname, '../../');

// Load env.test explicitly first
const envTestResult = dotenv.config({ path: resolve(projectRoot, 'env.test') });
if (envTestResult.parsed) {
    // Override any existing env vars with values from env.test
    Object.assign(process.env, envTestResult.parsed);
}

// Load .env but don't override what we set from env.test
dotenv.config({ path: resolve(projectRoot, '.env') });

// Verify env vars are loaded correctly
console.log('🔍 Env check - HEATWAVE_DATABASE:', process.env.HEATWAVE_DATABASE);
console.log('🔍 Env check - MYSQL_DATABASE:', process.env.MYSQL_DATABASE);

// Now import config after env vars are loaded (but it will also call dotenv.config())
// The values we set above will already be in process.env, so config() won't override them
import { config } from '../config';
import { MySportsFeedsClient } from '../services/MySportsFeedsClient';
import { DataService } from '../services/DataService';
import { DataTransformers } from '../services/DataTransformers';
import { heatwaveDataStorageService } from '../services/HeatWaveDataStorageService';
import { HeatWaveService } from '../services/HeatWaveClient';
import { logger } from '../utils/logger';
import {
    PlayerGameLogsApiResponse,
    InjuriesApiResponse,
    DfsProjectionsApiResponse,
    DailyDfsDataApiResponse,
    GameLineupApiResponse
} from '../types/api-schemas';

// Season start date
const SEASON_START_DATE = '2025-10-21';

/**
 * Get date range from start date to today
 */
function getDateRange(startDate: string): string[] {
    const dates: string[] = [];
    const start = new Date(startDate);
    const today = new Date();

    const current = new Date(start);
    while (current <= today) {
        // Format as YYYYMMDD for MySportsFeeds API
        const year = current.getFullYear();
        const month = String(current.getMonth() + 1).padStart(2, '0');
        const day = String(current.getDate()).padStart(2, '0');
        dates.push(`${year}${month}${day}`);
        current.setDate(current.getDate() + 1);
    }

    return dates;
}

/**
 * Transform player game logs to match MySQL schema
 */
function transformGameLogsForMySQL(apiData: PlayerGameLogsApiResponse): any[] {
    const gameLogs: any[] = [];

    if (apiData.playergamelogs && Array.isArray(apiData.playergamelogs)) {
        for (const log of apiData.playergamelogs) {
            const stats = log.stats || {};

            // Calculate fantasy points if not provided (standard formula)
            let fantasyPoints = 0;
            if (stats.FantasyPoints?.value !== undefined) {
                fantasyPoints = parseFloat(stats.FantasyPoints.value);
            } else {
                // Calculate: PTS*1 + REB*1.2 + AST*1.5 + STL*3 + BLK*3 - TO*1
                const pts = parseFloat(stats.Pts?.value || '0');
                const reb = parseFloat(stats.Reb?.value || '0');
                const ast = parseFloat(stats.Ast?.value || '0');
                const stl = parseFloat(stats.Stl?.value || '0');
                const blk = parseFloat(stats.Blk?.value || '0');
                const tov = parseFloat(stats.Tov?.value || '0');
                fantasyPoints = pts + (reb * 1.2) + (ast * 1.5) + (stl * 3) + (blk * 3) - tov;
            }

            const gameLog = {
                player_id: log.player.id,
                game_id: log.game.id,
                fantasy_points: fantasyPoints,
                minutes_played: parseInt(stats.Min?.value || '0'),
                field_goals_made: parseInt(stats.FgM?.value || '0'),
                field_goals_attempted: parseInt(stats.FgA?.value || '0'),
                three_pointers_made: parseInt(stats.Fg3M?.value || '0'),
                three_pointers_attempted: parseInt(stats.Fg3A?.value || '0'),
                free_throws_made: parseInt(stats.FtM?.value || '0'),
                free_throws_attempted: parseInt(stats.FtA?.value || '0'),
                rebounds: parseInt(stats.Reb?.value || '0'),
                assists: parseInt(stats.Ast?.value || '0'),
                steals: parseInt(stats.Stl?.value || '0'),
                blocks: parseInt(stats.Blk?.value || '0'),
                turnovers: parseInt(stats.Tov?.value || '0'),
                personal_fouls: parseInt(stats.Pf?.value || '0'),
                plus_minus: parseInt(stats.PlusMinus?.value || '0')
            };

            gameLogs.push(gameLog);
        }
    }

    return gameLogs;
}

/**
 * Transform injuries to match MySQL schema
 */
function transformInjuriesForMySQL(apiData: InjuriesApiResponse): any[] {
    const injuries: any[] = [];

    if (apiData.players && Array.isArray(apiData.players)) {
        for (const player of apiData.players) {
            if (player.currentInjury) {
                const injury = {
                    player_id: player.id,
                    injury_type: player.currentInjury.description || 'Unknown',
                    status: (player.currentInjury as any).status || player.currentRosterStatus || 'ACTIVE',
                    start_date: (player.currentInjury as any).injuryDate || null,
                    expected_return: (player.currentInjury as any).expectedReturn || null,
                    description: player.currentInjury.description || player.currentInjury.playingProbability || ''
                };

                injuries.push(injury);
            }
        }
    }

    return injuries;
}

/**
 * Transform DFS projections to match MySQL schema
 */
function transformDfsProjectionsForMySQL(apiData: DfsProjectionsApiResponse, _date: string): any[] {
    const projections: any[] = [];

    // API uses lowercase dfsprojections
    const projArray = (apiData as any).dfsprojections || [];

    if (Array.isArray(projArray)) {
        for (const projection of projArray) {
            const fantasyPoints = projection.fantasyPoints || [];

            // Use first fantasy point value or calculate from stats
            let projectedPoints = 0;
            if (fantasyPoints.length > 0 && fantasyPoints[0].points) {
                projectedPoints = parseFloat(fantasyPoints[0].points.toString());
            }

            const proj = {
                player_id: projection.player.id,
                game_id: projection.game.id,
                projected_fantasy_points: projectedPoints || null,
                salary: projection.salary || null,
                ownership_percentage: projection.ownershipPercentage || null,
                ceiling: null, // Not available in API response
                floor: null, // Not available in API response
                value_score: projection.salary && projectedPoints ? (projectedPoints / (projection.salary / 1000)) : null
            };

            projections.push(proj);
        }
    }

    return projections;
}

/**
 * Transform daily DFS data to match MySQL schema
 * Schema: player_id, game_id, fantasy_points, salary, ownership_percentage, slate_id, platform
 */
function transformDailyDfsForMySQL(apiData: DailyDfsDataApiResponse, _date: string): any[] {
    const dailyData: any[] = [];

    // Handle both dailydfsdata (API response)
    const dfsArray = (apiData as any).dailydfsdata || [];

    if (Array.isArray(dfsArray)) {
        for (const data of dfsArray) {
            const fantasyPoints = data.fantasyPoints || [];
            let fpValue: number | null = null;
            if (fantasyPoints.length > 0 && fantasyPoints[0].points) {
                fpValue = parseFloat(fantasyPoints[0].points.toString());
            }

            const daily = {
                player_id: data.player.id,
                game_id: data.game.id,
                fantasy_points: fpValue,
                salary: data.salary || null,
                ownership_percentage: data.ownershipPercentage || null,
                slate_id: null, // Not available in API response
                platform: null // Not available in API response
            };

            dailyData.push(daily);
        }
    }

    return dailyData;
}

/**
 * Transform game lineups to match MySQL schema
 */
function transformGameLineupsForMySQL(apiData: GameLineupApiResponse): any[] {
    const lineups: any[] = [];

    if (apiData.lineup) {
        const game = apiData.lineup.game;

        // Away team lineup
        if (apiData.lineup.awayTeamLineup && Array.isArray(apiData.lineup.awayTeamLineup)) {
            for (const lineupItem of apiData.lineup.awayTeamLineup) {
                lineups.push({
                    game_id: game.id,
                    team_id: game.awayTeam.id,
                    player_id: lineupItem.player.id,
                    position: lineupItem.position || null,
                    starter: lineupItem.starter || false,
                    minutes_played: null
                });
            }
        }

        // Home team lineup
        if (apiData.lineup.homeTeamLineup && Array.isArray(apiData.lineup.homeTeamLineup)) {
            for (const lineupItem of apiData.lineup.homeTeamLineup) {
                lineups.push({
                    game_id: game.id,
                    team_id: game.homeTeam.id,
                    player_id: lineupItem.player.id,
                    position: lineupItem.position || null,
                    starter: lineupItem.starter || false,
                    minutes_played: null
                });
            }
        }
    }

    return lineups;
}

/**
 * Store game logs in database
 */
async function storeGameLogs(gameLogs: any[], heatwaveService: any): Promise<{ created: number; errors: number }> {
    let created = 0;
    let errors = 0;

    for (const log of gameLogs) {
        try {
            // Check if exists using player_id and game_id
            const existing = await heatwaveService.queryOne(
                'SELECT id FROM player_game_logs WHERE player_id = ? AND game_id = ?',
                [log.player_id, log.game_id]
            );

            if (existing) {
                // Update existing
                await heatwaveService.query(
                    `UPDATE player_game_logs SET 
                     fantasy_points = ?, minutes_played = ?, field_goals_made = ?, field_goals_attempted = ?,
                     three_pointers_made = ?, three_pointers_attempted = ?, free_throws_made = ?,
                     free_throws_attempted = ?, rebounds = ?, assists = ?, steals = ?, blocks = ?,
                     turnovers = ?, personal_fouls = ?, plus_minus = ?
                     WHERE player_id = ? AND game_id = ?`,
                    [
                        log.fantasy_points, log.minutes_played, log.field_goals_made, log.field_goals_attempted,
                        log.three_pointers_made, log.three_pointers_attempted, log.free_throws_made,
                        log.free_throws_attempted, log.rebounds, log.assists, log.steals, log.blocks,
                        log.turnovers, log.personal_fouls, log.plus_minus,
                        log.player_id, log.game_id
                    ]
                );
            } else {
                // Insert new
                await heatwaveService.query(
                    `INSERT INTO player_game_logs (
                        player_id, game_id, fantasy_points, minutes_played,
                        field_goals_made, field_goals_attempted, three_pointers_made,
                        three_pointers_attempted, free_throws_made, free_throws_attempted,
                        rebounds, assists, steals, blocks, turnovers, personal_fouls, plus_minus
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
                    [
                        log.player_id, log.game_id, log.fantasy_points, log.minutes_played,
                        log.field_goals_made, log.field_goals_attempted, log.three_pointers_made,
                        log.three_pointers_attempted, log.free_throws_made, log.free_throws_attempted,
                        log.rebounds, log.assists, log.steals, log.blocks, log.turnovers, log.personal_fouls, log.plus_minus
                    ]
                );
                created++;
            }
        } catch (error: any) {
            logger.error(`Error storing game log for player ${log.player_id}, game ${log.game_id}:`, error);
            errors++;
        }
    }

    return { created, errors };
}

/**
 * Store injuries in database
 */
async function storeInjuries(injuries: any[], heatwaveService: any): Promise<{ created: number; errors: number }> {
    let created = 0;
    let errors = 0;

    for (const injury of injuries) {
        try {
            // First check if player exists (foreign key constraint)
            const playerExists = await heatwaveService.queryOne(
                'SELECT id FROM players WHERE id = ?',
                [injury.player_id]
            );

            if (!playerExists) {
                // Skip injuries for players that don't exist yet
                logger.debug(`Skipping injury for player ${injury.player_id} - player not in database`);
                continue;
            }

            // Check if injury exists using player_id
            const existing = await heatwaveService.queryOne(
                'SELECT id FROM injuries WHERE player_id = ?',
                [injury.player_id]
            );

            if (existing) {
                // Update existing
                await heatwaveService.query(
                    `UPDATE injuries SET 
                     injury_type = ?, status = ?, start_date = ?, expected_return = ?, description = ?
                     WHERE player_id = ?`,
                    [injury.injury_type, injury.status, injury.start_date, injury.expected_return, injury.description, injury.player_id]
                );
            } else {
                // Insert new
                await heatwaveService.query(
                    `INSERT INTO injuries (player_id, injury_type, status, start_date, expected_return, description)
                     VALUES (?, ?, ?, ?, ?, ?)`,
                    [injury.player_id, injury.injury_type, injury.status, injury.start_date, injury.expected_return, injury.description]
                );
                created++;
            }
        } catch (error: any) {
            logger.error(`Error storing injury for player ${injury.player_id}:`, error);
            errors++;
        }
    }

    return { created, errors };
}

/**
 * Store DFS projections in database
 */
async function storeDfsProjections(projections: any[], heatwaveService: any, urlDate: string): Promise<{ created: number; errors: number }> {
    let created = 0;
    let errors = 0;

    // Convert URL date (YYYYMMDD) to database format (YYYY-MM-DD)
    const dbDate = urlDate.length === 8
        ? `${urlDate.substring(0, 4)}-${urlDate.substring(4, 6)}-${urlDate.substring(6, 8)}`
        : urlDate;

    for (const proj of projections) {
        try {
            // Validate: Check that the game exists and its game_date matches the URL date
            const game = await heatwaveService.queryOne(
                'SELECT game_date FROM games WHERE id = ?',
                [proj.game_id]
            ) as { game_date: string | Date } | null;

            if (!game) {
                logger.debug(`Skipping DFS projection for player ${proj.player_id}, game ${proj.game_id} - game not found`);
                errors++;
                continue;
            }

            // Verify game date matches URL date
            const gameDateStr = game.game_date instanceof Date
                ? game.game_date.toISOString().split('T')[0]
                : game.game_date?.toString().split('T')[0];

            if (gameDateStr !== dbDate) {
                logger.debug(`Skipping DFS projection for player ${proj.player_id}, game ${proj.game_id} - game date ${gameDateStr} doesn't match URL date ${dbDate}`);
                errors++;
                continue;
            }

            // Check if exists using player_id and game_id
            const existing = await heatwaveService.queryOne(
                'SELECT id FROM dfs_projections WHERE player_id = ? AND game_id = ?',
                [proj.player_id, proj.game_id]
            );

            if (existing) {
                // Update existing
                await heatwaveService.query(
                    `UPDATE dfs_projections SET 
                     projected_fantasy_points = ?, salary = ?, ownership_percentage = ?,
                     ceiling = ?, floor = ?, value_score = ?
                     WHERE player_id = ? AND game_id = ?`,
                    [
                        proj.projected_fantasy_points, proj.salary, proj.ownership_percentage,
                        proj.ceiling, proj.floor, proj.value_score,
                        proj.player_id, proj.game_id
                    ]
                );
            } else {
                // Insert new
                await heatwaveService.query(
                    `INSERT INTO dfs_projections (
                        player_id, game_id, projected_fantasy_points, salary,
                        ownership_percentage, ceiling, floor, value_score
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
                    [
                        proj.player_id, proj.game_id, proj.projected_fantasy_points, proj.salary,
                        proj.ownership_percentage, proj.ceiling, proj.floor, proj.value_score
                    ]
                );
                created++;
            }
        } catch (error: any) {
            logger.error(`Error storing DFS projection for player ${proj.player_id}, game ${proj.game_id}:`, error);
            errors++;
        }
    }

    return { created, errors };
}

/**
 * Store daily DFS data in database
 */
async function storeDailyDfs(dailyData: any[], heatwaveService: any, urlDate: string): Promise<{ created: number; errors: number }> {
    let created = 0;
    let errors = 0;

    // Convert URL date (YYYYMMDD) to database format (YYYY-MM-DD)
    const dbDate = urlDate.length === 8
        ? `${urlDate.substring(0, 4)}-${urlDate.substring(4, 6)}-${urlDate.substring(6, 8)}`
        : urlDate;

    for (const daily of dailyData) {
        try {
            // Validate: Check that the game exists and its game_date matches the URL date
            const game = await heatwaveService.queryOne(
                'SELECT game_date FROM games WHERE id = ?',
                [daily.game_id]
            ) as { game_date: string | Date } | null;

            if (!game) {
                logger.debug(`Skipping daily DFS data for player ${daily.player_id}, game ${daily.game_id} - game not found`);
                errors++;
                continue;
            }

            // Verify game date matches URL date
            const gameDateStr = game.game_date instanceof Date
                ? game.game_date.toISOString().split('T')[0]
                : game.game_date?.toString().split('T')[0];

            if (gameDateStr !== dbDate) {
                logger.debug(`Skipping daily DFS data for player ${daily.player_id}, game ${daily.game_id} - game date ${gameDateStr} doesn't match URL date ${dbDate}`);
                errors++;
                continue;
            }

            // Check if exists using player_id and game_id
            const existing = await heatwaveService.queryOne(
                'SELECT id FROM daily_dfs_data WHERE player_id = ? AND game_id = ?',
                [daily.player_id, daily.game_id]
            );

            if (existing) {
                // Update existing
                await heatwaveService.query(
                    `UPDATE daily_dfs_data SET 
                     fantasy_points = ?, salary = ?, ownership_percentage = ?,
                     slate_id = ?, platform = ?
                     WHERE player_id = ? AND game_id = ?`,
                    [
                        daily.fantasy_points, daily.salary, daily.ownership_percentage,
                        daily.slate_id, daily.platform,
                        daily.player_id, daily.game_id
                    ]
                );
            } else {
                // Insert new
                await heatwaveService.query(
                    `INSERT INTO daily_dfs_data (
                        player_id, game_id, fantasy_points, salary,
                        ownership_percentage, slate_id, platform
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)`,
                    [
                        daily.player_id, daily.game_id, daily.fantasy_points, daily.salary,
                        daily.ownership_percentage, daily.slate_id, daily.platform
                    ]
                );
                created++;
            }
        } catch (error: any) {
            logger.error(`Error storing daily DFS data for player ${daily.player_id}, game ${daily.game_id}:`, error);
            errors++;
        }
    }

    return { created, errors };
}

/**
 * Store game lineups in database
 */
async function storeGameLineups(lineups: any[], heatwaveService: any): Promise<{ created: number; errors: number }> {
    let created = 0;
    let errors = 0;

    for (const lineup of lineups) {
        try {
            // Check if exists using game_id, team_id, and player_id
            const existing = await heatwaveService.queryOne(
                'SELECT id FROM game_lineups WHERE game_id = ? AND team_id = ? AND player_id = ?',
                [lineup.game_id, lineup.team_id, lineup.player_id]
            );

            if (existing) {
                // Update existing
                await heatwaveService.query(
                    `UPDATE game_lineups SET 
                     position = ?, starter = ?, minutes_played = ?
                     WHERE game_id = ? AND team_id = ? AND player_id = ?`,
                    [lineup.position, lineup.starter, lineup.minutes_played, lineup.game_id, lineup.team_id, lineup.player_id]
                );
            } else {
                // Insert new
                await heatwaveService.query(
                    `INSERT INTO game_lineups (game_id, team_id, player_id, position, starter, minutes_played)
                     VALUES (?, ?, ?, ?, ?, ?)`,
                    [lineup.game_id, lineup.team_id, lineup.player_id, lineup.position, lineup.starter, lineup.minutes_played]
                );
                created++;
            }
        } catch (error: any) {
            logger.error(`Error storing lineup for game ${lineup.game_id}, team ${lineup.team_id}, player ${lineup.player_id}:`, error);
            errors++;
        }
    }

    return { created, errors };
}

/**
 * API abbreviation to database abbreviation mapping
 * Some teams have different abbreviations in the API vs database
 */
const API_ABBREVIATION_MAP: Record<string, string> = {
    'OKL': 'OKC',  // Oklahoma City Thunder: API uses OKL, DB uses OKC
    'BRO': 'BKN',  // Brooklyn Nets: API uses BRO, DB uses BKN
};

/**
 * Normalize API abbreviation to database abbreviation
 */
function normalizeAbbreviation(apiAbbrev: string): string {
    return API_ABBREVIATION_MAP[apiAbbrev.toUpperCase()] || apiAbbrev.toUpperCase();
}

/**
 * Load team ID mapping from database (abbreviation -> database team ID)
 */
async function loadTeamIdMapping(heatwaveService: any): Promise<Map<string, number>> {
    const teamMap = new Map<string, number>();

    try {
        const teams = await heatwaveService.query(
            'SELECT id, abbreviation FROM teams'
        ) as Array<{ id: number; abbreviation: string }>;

        for (const team of teams) {
            if (team.abbreviation) {
                const dbAbbrev = team.abbreviation.toUpperCase();
                teamMap.set(dbAbbrev, team.id);

                // Also map any API abbreviations that differ for this team
                for (const [apiAbbrev, mappedAbbrev] of Object.entries(API_ABBREVIATION_MAP)) {
                    if (mappedAbbrev.toUpperCase() === dbAbbrev) {
                        teamMap.set(apiAbbrev.toUpperCase(), team.id);
                    }
                }
            }
        }

        logger.info(`✅ Loaded ${teamMap.size} teams for ID mapping (including API abbreviation aliases)`);
    } catch (error) {
        logger.error('❌ Failed to load team ID mapping:', error);
    }

    return teamMap;
}

/**
 * Map API team IDs to database team IDs using abbreviation mapping
 */
function mapTeamIds(
    games: any[],
    teams: any[],
    teamMap: Map<string, number>
): { games: any[]; teams: any[] } {
    const mappedGames = games.map(game => {
        // Get team abbreviations from the teams array
        const homeTeam = teams.find(t => t.id === game.home_team_id);
        const awayTeam = teams.find(t => t.id === game.away_team_id);

        if (homeTeam?.abbreviation) {
            const normalizedAbbrev = normalizeAbbreviation(homeTeam.abbreviation);
            if (teamMap.has(normalizedAbbrev)) {
                game.home_team_id = teamMap.get(normalizedAbbrev);
            } else {
                logger.warn(`⚠️ No database team ID found for home team abbreviation: ${homeTeam.abbreviation} (normalized: ${normalizedAbbrev})`);
                game.home_team_id = null;
            }
        }

        if (awayTeam?.abbreviation) {
            const normalizedAbbrev = normalizeAbbreviation(awayTeam.abbreviation);
            if (teamMap.has(normalizedAbbrev)) {
                game.away_team_id = teamMap.get(normalizedAbbrev);
            } else {
                logger.warn(`⚠️ No database team ID found for away team abbreviation: ${awayTeam.abbreviation} (normalized: ${normalizedAbbrev})`);
                game.away_team_id = null;
            }
        }

        return game;
    });

    // Also map team IDs in the teams array (use API ID temporarily, but store with database ID)
    const mappedTeams = teams.map(team => {
        if (team.abbreviation && teamMap.has(team.abbreviation.toUpperCase())) {
            const dbTeamId = teamMap.get(team.abbreviation.toUpperCase());
            // Keep original for reference but we'll use database ID
            return { ...team, _api_id: team.id, id: dbTeamId };
        }
        return team;
    });

    return { games: mappedGames, teams: mappedTeams };
}


/**
 * Main function to fetch and store current season data
 */
async function fetchCurrentSeasonData() {
    logger.info('🚀 Starting current season data fetch and import...');
    logger.info(`📅 Date range: ${SEASON_START_DATE} to today`);

    // Create new instance to ensure it uses the correct config
    const heatwaveService = new HeatWaveService();

    logger.info(`🔍 Config DB: ${config.heatwave.database}`);
    logger.info(`🔍 Config Host: ${config.heatwave.host}`);
    logger.info(`🔍 Process.env HEATWAVE_DATABASE: ${process.env.HEATWAVE_DATABASE}`);

    // Test database connection (use our new instance)
    const connected = await heatwaveService.testConnection();
    if (!connected) {
        logger.error('❌ Failed to connect to Oracle Cloud MySQL HeatWave');
        process.exit(1);
    }

    // Load team ID mapping once at startup
    const teamIdMap = await loadTeamIdMapping(heatwaveService);
    if (teamIdMap.size === 0) {
        logger.warn('⚠️ No teams found in database - team ID mapping will not work');
    }

    // Initialize API client and data service
    const apiClient = new MySportsFeedsClient(config.mysportsfeeds);
    const dataService = new DataService(apiClient);

    // Use "current" for the season instead of calculating
    const season = 'current';
    logger.info(`🏀 Season: ${season}`);

    // Get date range
    const dates = getDateRange(SEASON_START_DATE);
    logger.info(`📋 Processing ${dates.length} dates...`);

    // Statistics
    const stats = {
        gameLogs: { created: 0, errors: 0 },
        injuries: { created: 0, errors: 0 },
        dfsProjections: { created: 0, errors: 0 },
        dailyDfs: { created: 0, errors: 0 },
        lineups: { created: 0, errors: 0 },
        games: { created: 0, errors: 0 }
    };

    // First, sync injuries (once, not per date)
    logger.info('🏥 Fetching injuries...');
    try {
        const injuriesData = await dataService.getAllInjuries();
        const injuries = transformInjuriesForMySQL(injuriesData);
        if (injuries.length > 0) {
            const result = await storeInjuries(injuries, heatwaveService);
            stats.injuries = result;
            logger.info(`✅ Injuries: ${result.created} created, ${result.errors} errors`);
        } else {
            logger.info('⚠️ No injuries found');
        }
    } catch (error) {
        logger.error('❌ Failed to fetch injuries:', error);
    }

    // Process each date
    for (let i = 0; i < dates.length; i++) {
        const dateStr = dates[i];
        const dateDisplay = `${dateStr.substring(0, 4)}-${dateStr.substring(4, 6)}-${dateStr.substring(6, 8)}`;
        logger.info(`\n📅 Processing date ${i + 1}/${dates.length}: ${dateDisplay}`);

        try {
            // 1. Fetch and store games
            logger.info('   🏀 Fetching games...');
            try {
                const gamesData = await dataService.getDailyGames(season, dateStr);
                if (gamesData && gamesData.games && gamesData.games.length > 0) {
                    const { games: apiGames, teams: apiTeams } = DataTransformers.transformGames(gamesData);

                    logger.info(`   📋 Found ${apiGames.length} games for ${dateDisplay}`);

                    // Store teams first (they may have API IDs, but we'll handle mapping)
                    if (apiTeams.length > 0) {
                        await heatwaveDataStorageService.storeTeams(apiTeams);
                    }

                    // Map API team IDs to database team IDs using abbreviations
                    const { games } = mapTeamIds(apiGames, apiTeams, teamIdMap);

                    // Filter out games where we couldn't map team IDs
                    const validGames = games.filter(g => g.home_team_id && g.away_team_id);
                    const skippedGames = games.length - validGames.length;
                    if (skippedGames > 0) {
                        logger.warn(`   ⚠️ Skipped ${skippedGames} games due to unmapped team IDs`);
                    }

                    if (validGames.length > 0) {
                        const gamesResult = await heatwaveDataStorageService.storeGames(validGames);
                        stats.games.created += gamesResult.created;
                        stats.games.errors += gamesResult.errors;
                        logger.info(`   ✅ Games: ${gamesResult.created} created, ${gamesResult.errors} errors`);

                        // 2. Fetch player game logs
                        logger.info('   📊 Fetching player game logs...');
                        try {
                            const gameLogsData = await dataService.getPlayerGameLogs(season, dateStr);
                            const gameLogs = transformGameLogsForMySQL(gameLogsData);
                            if (gameLogs.length > 0) {
                                const result = await storeGameLogs(gameLogs, heatwaveService);
                                stats.gameLogs.created += result.created;
                                stats.gameLogs.errors += result.errors;
                                logger.info(`   ✅ Game Logs: ${result.created} created, ${result.errors} errors`);
                            }
                        } catch (error: any) {
                            logger.warn(`   ⚠️ Failed to fetch game logs for ${dateDisplay}:`, error.message);
                        }

                        // 3. Fetch game lineups for each game (only if we have games)
                        logger.info('   👥 Fetching game lineups...');
                        try {
                            const lineupsData = await dataService.getAllLineupsForDate(season, dateStr);
                            let totalLineupsCreated = 0;
                            for (const lineupData of lineupsData) {
                                const lineups = transformGameLineupsForMySQL(lineupData);
                                if (lineups.length > 0) {
                                    // Map team IDs in lineups using the team mapping
                                    const mappedLineups = lineups.map(lineup => {
                                        // Get the game to find which team this lineup belongs to
                                        const game = validGames.find(g => g.id === lineup.game_id);
                                        if (game) {
                                            // Check if this lineup's team_id matches home or away in the API response
                                            // We need to look up the original API game to get abbreviations
                                            const apiGame = apiGames.find(g => g.id === lineup.game_id);
                                            if (apiGame) {
                                                // Determine which team by checking home/away team IDs from API
                                                // The lineup team_id comes from API, so we need to map it
                                                const apiTeam = apiTeams.find(t => t.id === lineup.team_id);
                                                if (apiTeam?.abbreviation) {
                                                    const normalizedAbbrev = normalizeAbbreviation(apiTeam.abbreviation);
                                                    if (teamIdMap.has(normalizedAbbrev)) {
                                                        lineup.team_id = teamIdMap.get(normalizedAbbrev)!;
                                                    } else {
                                                        // Can't map, set to null to skip
                                                        lineup.team_id = null as any;
                                                    }
                                                } else {
                                                    lineup.team_id = null as any;
                                                }
                                            }
                                        }
                                        return lineup;
                                    }).filter(l => l.team_id !== null);

                                    if (mappedLineups.length > 0) {
                                        const result = await storeGameLineups(mappedLineups, heatwaveService);
                                        stats.lineups.created += result.created;
                                        stats.lineups.errors += result.errors;
                                        totalLineupsCreated += mappedLineups.length;
                                    }
                                }
                            }
                            if (lineupsData.length > 0) {
                                logger.info(`   ✅ Lineups: ${totalLineupsCreated} processed`);
                            }
                        } catch (error: any) {
                            logger.warn(`   ⚠️ Failed to fetch lineups for ${dateDisplay}:`, error.message);
                        }

                        // 4. Fetch DFS projections
                        logger.info('   💰 Fetching DFS projections...');
                        try {
                            const dfsProjData = await dataService.getDfsProjections(season, dateStr);
                            const projections = transformDfsProjectionsForMySQL(dfsProjData, dateDisplay);
                            if (projections.length > 0) {
                                const result = await storeDfsProjections(projections, heatwaveService, dateStr);
                                stats.dfsProjections.created += result.created;
                                stats.dfsProjections.errors += result.errors;
                                logger.info(`   ✅ DFS Projections: ${result.created} created, ${result.errors} errors`);
                            }
                        } catch (error: any) {
                            logger.warn(`   ⚠️ Failed to fetch DFS projections for ${dateDisplay}:`, error.message);
                        }

                        // 5. Fetch daily DFS data
                        logger.info('   📈 Fetching daily DFS data...');
                        try {
                            const dailyDfsData = await dataService.getDailyDfs(season, dateStr);
                            const dailyData = transformDailyDfsForMySQL(dailyDfsData, dateDisplay);
                            if (dailyData.length > 0) {
                                const result = await storeDailyDfs(dailyData, heatwaveService, dateStr);
                                stats.dailyDfs.created += result.created;
                                stats.dailyDfs.errors += result.errors;
                                logger.info(`   ✅ Daily DFS: ${result.created} created, ${result.errors} errors`);
                            }
                        } catch (error: any) {
                            logger.warn(`   ⚠️ Failed to fetch daily DFS for ${dateDisplay}:`, error.message);
                        }
                    } else {
                        logger.info(`   ⏭️ No valid games found for ${dateDisplay} (all games had unmapped team IDs)`);
                    }
                } else {
                    logger.info(`   ⏭️ No games data returned for ${dateDisplay}`);
                }
            } catch (error: any) {
                logger.warn(`   ⚠️ Failed to fetch games for ${dateDisplay}:`, error.message);
                // Continue to next date even if this one fails
            }

            // Rate limiting delay
            await new Promise(resolve => setTimeout(resolve, config.mysportsfeeds.rateLimitDelay));
        } catch (error: any) {
            logger.error(`   ❌ Error processing date:`, error.message);
        }
    }

    // Print summary
    logger.info('\n📊 Import Summary:');
    logger.info('='.repeat(60));
    logger.info(`Games:              ${stats.games.created} created, ${stats.games.errors} errors`);
    logger.info(`Player Game Logs:   ${stats.gameLogs.created} created, ${stats.gameLogs.errors} errors`);
    logger.info(`Injuries:           ${stats.injuries.created} created, ${stats.injuries.errors} errors`);
    logger.info(`DFS Projections:    ${stats.dfsProjections.created} created, ${stats.dfsProjections.errors} errors`);
    logger.info(`Daily DFS Data:     ${stats.dailyDfs.created} created, ${stats.dailyDfs.errors} errors`);
    logger.info(`Game Lineups:       ${stats.lineups.created} created, ${stats.lineups.errors} errors`);
    logger.info('='.repeat(60));
    logger.info('🎉 Current season data import completed!');

    // Close database connection
    await heatwaveService.close();

    // Also close the heatwaveDataStorageService's connection
    // (it uses the same service internally)
}

// Run the script
if (require.main === module) {
    fetchCurrentSeasonData()
        .then(() => {
            logger.info('✅ Script completed successfully');
            process.exit(0);
        })
        .catch((error) => {
            logger.error('❌ Script failed:', error);
            process.exit(1);
        });
}

export { fetchCurrentSeasonData };

