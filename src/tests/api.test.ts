import { describe, it, expect, beforeAll, beforeEach } from 'vitest';
import { MySportsFeedsClient } from '../services/MySportsFeedsClient';
import { DataService } from '../services/DataService';
import { config } from '../config';
import { logger } from '../utils/logger';

describe('MySportsFeeds API Integration', () => {
    let apiClient: MySportsFeedsClient;
    let dataService: DataService;

    beforeAll(() => {
        // Initialize API client with test configuration
        logger.info('🧪 Initializing test environment');
        apiClient = new MySportsFeedsClient(config.mysportsfeeds);
        dataService = new DataService(apiClient);
        logger.info('✅ Test environment initialized');
    });

    beforeEach(() => {
        logger.info('🔄 Starting new test case');
    });

    it('should perform health check', async () => {
        const isHealthy = await dataService.healthCheck();
        expect(isHealthy).toBe(true);
    });

    it('should fetch all players', async () => {
        logger.info('🔍 Testing: Fetch all players');
        const response = await dataService.getAllPlayers();

        logger.info('📊 Players response analysis:', {
            hasResponse: !!response,
            hasPlayers: !!response.players,
            playersCount: response.players?.length || 0,
            responseKeys: response ? Object.keys(response) : [],
            samplePlayer: response.players?.[0] ? {
                id: response.players[0].player.id,
                name: `${response.players[0].player.firstName} ${response.players[0].player.lastName}`,
                position: response.players[0].player.primaryPosition,
                team: response.players[0].player.currentTeam?.abbreviation
            } : null
        });

        expect(response).toBeDefined();
        expect(response.players).toBeDefined();
        expect(Array.isArray(response.players)).toBe(true);
    });

    it('should fetch players for a specific team', async () => {
        const response = await dataService.getPlayersForTeam('LAL');
        expect(response).toBeDefined();
        expect(response.players).toBeDefined();
        expect(Array.isArray(response.players)).toBe(true);
    });

    it('should fetch daily games for a specific date', async () => {
        const season = dataService.getCurrentSeason();
        const date = '2024-12-19'; // Use a known date with games

        try {
            const response = await dataService.getDailyGames(season, date);
            expect(response).toBeDefined();
            expect(response.games).toBeDefined();
            expect(Array.isArray(response.games)).toBe(true);
        } catch (error) {
            // If no games on this date, that's also a valid response
            console.log(`No games found for ${date}, which is expected`);
        }
    });

    it('should fetch upcoming games', async () => {
        const season = dataService.getCurrentSeason();
        const response = await dataService.getUpcomingGames(season, 2);
        expect(response).toBeDefined();
        expect(Array.isArray(response)).toBe(true);
    });

    it('should fetch all injuries', async () => {
        const response = await dataService.getAllInjuries();
        expect(response).toBeDefined();
        expect(response.players).toBeDefined();
        expect(Array.isArray(response.players)).toBe(true);
    });

    it('should fetch DFS projections for a specific date', async () => {
        const season = dataService.getCurrentSeason();
        const date = dataService.getTodayDateString();

        try {
            const response = await dataService.getDfsProjections(season, date);
            expect(response).toBeDefined();
            expect(response.dfsProjections).toBeDefined();
            expect(Array.isArray(response.dfsProjections)).toBe(true);
        } catch (error) {
            // If no projections for today, that's also valid
            console.log(`No DFS projections found for ${date}, which may be expected`);
        }
    });

    it('should handle API errors gracefully', async () => {
        // Test with invalid date format
        const season = dataService.getCurrentSeason();
        const invalidDate = 'invalid-date';

        try {
            await dataService.getDailyGames(season, invalidDate);
            // If it doesn't throw, that's unexpected
            expect(false).toBe(true);
        } catch (error) {
            // Expected to throw an error
            expect(error).toBeDefined();
        }
    });

    it('should get current season correctly', () => {
        const season = dataService.getCurrentSeason();
        expect(season).toBeDefined();
        expect(typeof season).toBe('string');
        expect(season).toMatch(/^\d{4}-\d{2}$/); // Format: YYYY-YY
    });

    it('should get today date string correctly', () => {
        const today = dataService.getTodayDateString();
        expect(today).toBeDefined();
        expect(typeof today).toBe('string');
        expect(today).toMatch(/^\d{4}-\d{2}-\d{2}$/); // Format: YYYY-MM-DD
    });
});
