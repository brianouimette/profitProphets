import { DataService } from './DataService';
import { dataStorageService } from './DataStorageService';
import { DataTransformers } from './DataTransformers';
import { logger } from '../utils/logger';
// Remove unused import

export class DataSyncService {
    private dataService: DataService;

    constructor(dataService: DataService) {
        this.dataService = dataService;
    }

    /**
     * Sync all players data
     */
    async syncPlayers(): Promise<void> {
        const startTime = Date.now();
        logger.info('Starting players sync...');

        try {
            // Fetch players from API
            const apiData = await this.dataService.getAllPlayers();

            // Transform data
            const { players, teams } = DataTransformers.transformPlayers(apiData);

            // Store teams first (for foreign key references)
            if (teams.length > 0) {
                await dataStorageService.storeTeams(teams);
            }

            // Store players
            const result = await dataStorageService.storePlayers(players);

            // Log sync operation
            const duration = Date.now() - startTime;
            await dataStorageService.logSyncOperation(
                'players',
                new Date().toISOString().split('T')[0],
                players.length,
                result.created,
                result.updated,
                result.errors,
                duration,
                result.errors === 0 ? 'SUCCESS' : result.errors < players.length ? 'PARTIAL' : 'FAILED'
            );

            logger.info(`Players sync completed: ${result.created} created, ${result.updated} updated, ${result.errors} errors`);
        } catch (error) {
            logger.error('Players sync failed:', error);

            const duration = Date.now() - startTime;
            await dataStorageService.logSyncOperation(
                'players',
                new Date().toISOString().split('T')[0],
                0,
                0,
                0,
                0,
                duration,
                'FAILED'
            );

            throw error;
        }
    }

    /**
     * Sync games data for a specific date
     */
    async syncGames(date: string): Promise<void> {
        const startTime = Date.now();
        logger.info(`Starting games sync for ${date}...`);

        try {
            // Fetch games from API
            const season = this.dataService.getCurrentSeason();
            const apiData = await this.dataService.getDailyGames(season, date);

            // Transform data
            const { games, teams, venues } = DataTransformers.transformGames(apiData);

            // Store venues first
            if (venues.length > 0) {
                // Note: We'd need to add a storeVenues method to DataStorageService
                logger.info(`Found ${venues.length} venues (not storing yet - need to implement storeVenues)`);
            }

            // Store teams
            if (teams.length > 0) {
                await dataStorageService.storeTeams(teams);
            }

            // Store games
            const result = await dataStorageService.storeGames(games);

            // Log sync operation
            const duration = Date.now() - startTime;
            await dataStorageService.logSyncOperation(
                'games',
                date,
                games.length,
                result.created,
                result.updated,
                result.errors,
                duration,
                result.errors === 0 ? 'SUCCESS' : result.errors < games.length ? 'PARTIAL' : 'FAILED'
            );

            logger.info(`Games sync completed: ${result.created} created, ${result.updated} updated, ${result.errors} errors`);
        } catch (error) {
            logger.error(`Games sync failed for ${date}:`, error);

            const duration = Date.now() - startTime;
            await dataStorageService.logSyncOperation(
                'games',
                date,
                0,
                0,
                0,
                0,
                duration,
                'FAILED'
            );

            throw error;
        }
    }

    /**
     * Sync injuries data
     */
    async syncInjuries(): Promise<void> {
        const startTime = Date.now();
        logger.info('Starting injuries sync...');

        try {
            // Fetch injuries from API
            const apiData = await this.dataService.getAllInjuries();

            // Transform data
            const injuries = DataTransformers.transformInjuries(apiData);

            // Store injuries
            const result = await dataStorageService.storeInjuries(injuries);

            // Log sync operation
            const duration = Date.now() - startTime;
            await dataStorageService.logSyncOperation(
                'injuries',
                new Date().toISOString().split('T')[0],
                injuries.length,
                result.created,
                result.updated,
                result.errors,
                duration,
                result.errors === 0 ? 'SUCCESS' : result.errors < injuries.length ? 'PARTIAL' : 'FAILED'
            );

            logger.info(`Injuries sync completed: ${result.created} created, ${result.updated} updated, ${result.errors} errors`);
        } catch (error) {
            logger.error('Injuries sync failed:', error);

            const duration = Date.now() - startTime;
            await dataStorageService.logSyncOperation(
                'injuries',
                new Date().toISOString().split('T')[0],
                0,
                0,
                0,
                0,
                duration,
                'FAILED'
            );

            throw error;
        }
    }

    /**
     * Sync DFS projections for a specific date
     */
    async syncDfsProjections(date: string): Promise<void> {
        const startTime = Date.now();
        logger.info(`Starting DFS projections sync for ${date}...`);

        try {
            // Fetch DFS projections from API
            const season = this.dataService.getCurrentSeason();
            const apiData = await this.dataService.getDfsProjections(season, date);

            // Transform data
            const projections = DataTransformers.transformDfsProjections(apiData, date);

            // Store projections
            const result = await dataStorageService.storeDfsProjections(projections);

            // Log sync operation
            const duration = Date.now() - startTime;
            await dataStorageService.logSyncOperation(
                'dfs_projections',
                date,
                projections.length,
                result.created,
                result.updated,
                result.errors,
                duration,
                result.errors === 0 ? 'SUCCESS' : result.errors < projections.length ? 'PARTIAL' : 'FAILED'
            );

            logger.info(`DFS projections sync completed: ${result.created} created, ${result.updated} updated, ${result.errors} errors`);
        } catch (error) {
            logger.error(`DFS projections sync failed for ${date}:`, error);

            const duration = Date.now() - startTime;
            await dataStorageService.logSyncOperation(
                'dfs_projections',
                date,
                0,
                0,
                0,
                0,
                duration,
                'FAILED'
            );

            throw error;
        }
    }

    /**
     * Sync all data for today
     */
    async syncToday(): Promise<void> {
        const today = new Date().toISOString().split('T')[0];
        logger.info(`Starting full sync for ${today}...`);

        try {
            // Sync in order of dependencies
            await this.syncPlayers();
            await this.syncGames(today);
            await this.syncInjuries();
            await this.syncDfsProjections(today);

            logger.info(`Full sync completed for ${today}`);
        } catch (error) {
            logger.error(`Full sync failed for ${today}:`, error);
            throw error;
        }
    }

    /**
     * Get sync status
     */
    async getSyncStatus(): Promise<{
        lastSync: any;
        health: any;
        recentSyncs: any[];
    }> {
        try {
            const [lastSync, recentSyncs] = await Promise.all([
                dataStorageService.getSyncHistory(1).then(syncs => syncs[0] || null),
                dataStorageService.getSyncHistory(10)
            ]);

            return {
                lastSync,
                health: { connected: true, tables: [] }, // Simplified health status
                recentSyncs
            };
        } catch (error) {
            logger.error('Failed to get sync status:', error);
            return {
                lastSync: null,
                health: { connected: false, tables: [] },
                recentSyncs: []
            };
        }
    }
}
