#!/usr/bin/env tsx

import { config, validateConfig } from '../config';
import { MySportsFeedsClient } from '../services/MySportsFeedsClient';
import { DataService } from '../services/DataService';
import { logger } from '../utils/logger';

async function testApiIntegration() {
    try {
        // Validate configuration
        validateConfig();
        logger.info('Configuration validated successfully');

        // Initialize services
        const apiClient = new MySportsFeedsClient(config.mysportsfeeds);
        const dataService = new DataService(apiClient);

        logger.info('Starting API integration test...');

        // Test health check
        logger.info('Testing health check...');
        const isHealthy = await dataService.healthCheck();
        logger.info(`Health check result: ${isHealthy ? 'PASSED' : 'FAILED'}`);

        if (!isHealthy) {
            logger.error('API health check failed. Please check your credentials and network connection.');
            process.exit(1);
        }

        // Test fetching players
        logger.info('Testing players fetch...');
        const playersResponse = await dataService.getAllPlayers();
        logger.info(`Players fetched: ${playersResponse.players?.length || 0}`);

        if (playersResponse.players && playersResponse.players.length > 0) {
            logger.info('Sample player data:', {
                firstPlayer: {
                    id: playersResponse.players[0].player.id,
                    name: `${playersResponse.players[0].player.firstName} ${playersResponse.players[0].player.lastName}`,
                    position: playersResponse.players[0].player.primaryPosition,
                    team: playersResponse.players[0].player.currentTeam?.abbreviation
                }
            });
        }

        // Test fetching current season
        const currentSeason = dataService.getCurrentSeason();
        logger.info(`Current season: ${currentSeason}`);

        // Test fetching today's date
        const today = dataService.getTodayDateString();
        logger.info(`Today's date: ${today}`);

        // Test fetching upcoming games
        logger.info('Testing upcoming games fetch...');
        const upcomingGames = await dataService.getUpcomingGames(currentSeason, 2);
        logger.info(`Upcoming games found: ${upcomingGames.length}`);

        // Test fetching injuries
        logger.info('Testing injuries fetch...');
        const injuriesResponse = await dataService.getAllInjuries();
        logger.info(`Injuries fetched: ${injuriesResponse.players?.length || 0}`);

        // Test fetching DFS data for today
        logger.info('Testing DFS data fetch...');
        try {
            const dfsResponse = await dataService.getDfsProjections(currentSeason, today);
            logger.info(`DFS projections fetched: ${dfsResponse.dfsProjections?.length || 0}`);
        } catch (error) {
            logger.warn('DFS projections not available for today (this may be normal)');
        }

        logger.info('API integration test completed successfully!');
        process.exit(0);

    } catch (error) {
        logger.error('API integration test failed:', error);
        process.exit(1);
    }
}

// Run the test
testApiIntegration();
