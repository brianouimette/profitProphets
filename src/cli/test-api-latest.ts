#!/usr/bin/env tsx

import { config, validateConfig } from '../config';
import { MySportsFeedsClient } from '../services/MySportsFeedsClient';
import { DataService } from '../services/DataService';
import { logger } from '../utils/logger';

async function testApiIntegrationWithLatest() {
    try {
        // Validate configuration
        validateConfig();
        logger.info('Configuration validated successfully');

        // Initialize services
        const apiClient = new MySportsFeedsClient(config.mysportsfeeds);
        const dataService = new DataService(apiClient);

        logger.info('Starting API integration test with LATEST season...');

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

        // Use 'latest' instead of current season logic
        const seasonToUse = 'latest';
        logger.info(`Using season: ${seasonToUse}`);

        // Test fetching today's date
        const today = dataService.getTodayDateString();
        logger.info(`Today's date: ${today}`);

        // Test fetching upcoming games with latest season
        logger.info('Testing upcoming games fetch with latest season...');
        try {
            const upcomingGames = await dataService.getUpcomingGames(seasonToUse, 2);
            logger.info(`Upcoming games found: ${upcomingGames.length}`);
        } catch (error) {
            logger.warn('Upcoming games not available with latest season:', error instanceof Error ? error.message : String(error));
        }

        // Test fetching injuries
        logger.info('Testing injuries fetch...');
        const injuriesResponse = await dataService.getAllInjuries();
        logger.info(`Injuries fetched: ${injuriesResponse.players?.length || 0}`);

        // Test fetching DFS data for today with latest season
        logger.info('Testing DFS data fetch with latest season...');
        try {
            const dfsResponse = await dataService.getDfsProjections(seasonToUse, today);
            logger.info(`DFS projections fetched: ${dfsResponse.dfsProjections?.length || 0}`);
        } catch (error) {
            logger.warn('DFS projections not available with latest season:', error instanceof Error ? error.message : String(error));
        }

        // Test fetching daily games with latest season
        logger.info('Testing daily games fetch with latest season...');
        try {
            const dailyGames = await dataService.getDailyGames(seasonToUse, today);
            logger.info(`Daily games found: ${dailyGames.games?.length || 0}`);
        } catch (error) {
            logger.warn('Daily games not available with latest season:', error instanceof Error ? error.message : String(error));
        }

        // Test with a known date from the latest season (try a few dates)
        logger.info('Testing with historical dates from latest season...');
        const testDates = [
            '2025-01-15', // Mid-season date
            '2025-02-15', // Another mid-season date
            '2025-03-15'  // Late season date
        ];

        for (const testDate of testDates) {
            try {
                logger.info(`Testing DFS projections for ${testDate}...`);
                const dfsResponse = await dataService.getDfsProjections(seasonToUse, testDate);
                logger.info(`✅ DFS projections found for ${testDate}: ${dfsResponse.dfsProjections?.length || 0}`);
                break; // Found data, stop testing other dates
            } catch (error) {
                logger.warn(`❌ No DFS data for ${testDate}: ${error instanceof Error ? error.message : String(error)}`);
            }
        }

        logger.info('API integration test with LATEST season completed successfully!');
        process.exit(0);

    } catch (error) {
        logger.error('API integration test failed:', error);
        process.exit(1);
    }
}

// Run the test
testApiIntegrationWithLatest();
