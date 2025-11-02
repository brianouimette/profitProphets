import { heatwaveService } from '../services/HeatWaveClient';
import { dataStorageService } from '../services/DataStorageService';
import { DataSyncService } from '../services/DataSyncService';
import { MySportsFeedsClient } from '../services/MySportsFeedsClient';
import { DataService } from '../services/DataService';
import { config } from '../config';
import { logger } from '../utils/logger';

async function testSupabaseIntegration() {
    logger.info('🧪 Starting Supabase integration test...');

    try {
        // Test 1: Database connection
        logger.info('1. Testing database connection...');
        const isConnected = await heatwaveService.testConnection();
        if (!isConnected) {
            throw new Error('Database connection failed');
        }
        logger.info('✅ Database connection successful');

        // Test 2: Health status
        logger.info('2. Testing database health status...');
        const health = await heatwaveService.getHealthStatus();
        logger.info('📊 Database health status:', {
            connected: health.connected,
            tablesCount: health.tables.length,
            lastSync: health.lastSync
        });

        // Test 3: Initialize data sync service
        logger.info('3. Initializing data sync service...');
        const apiClient = new MySportsFeedsClient(config.mysportsfeeds);
        const dataService = new DataService(apiClient);
        const dataSyncService = new DataSyncService(dataService);
        logger.info('✅ Data sync service initialized');

        // Test 4: Test API connection
        logger.info('4. Testing API connection...');
        const apiHealthy = await dataService.healthCheck();
        if (!apiHealthy) {
            throw new Error('API connection failed');
        }
        logger.info('✅ API connection successful');

        // Test 5: Sync players (small test)
        logger.info('5. Testing players sync (limited to 5 players)...');
        try {
            // Override the getPlayers method temporarily to limit results
            const originalGetPlayers = dataService.getAllPlayers;
            dataService.getAllPlayers = async () => {
                const fullData = await originalGetPlayers.call(dataService);
                if (fullData.players && Array.isArray(fullData.players)) {
                    return {
                        ...fullData,
                        players: fullData.players.slice(0, 5) // Limit to 5 players for testing
                    };
                }
                return fullData;
            };

            await dataSyncService.syncPlayers();
            logger.info('✅ Players sync test completed');
        } catch (error) {
            logger.error('❌ Players sync test failed:', error);
        }

        // Test 6: Get active players from database
        logger.info('6. Testing database queries...');
        const activePlayers = await dataStorageService.getActivePlayers();
        logger.info(`📊 Found ${activePlayers.length} active players in database`);

        if (activePlayers.length > 0) {
            logger.info('Sample player from database:', {
                id: activePlayers[0].id,
                name: `${activePlayers[0].first_name} ${activePlayers[0].last_name}`,
                position: activePlayers[0].primary_position,
                team_id: activePlayers[0].current_team_id
            });
        }

        // Test 7: Get sync history
        logger.info('7. Testing sync history...');
        const syncHistory = await dataStorageService.getSyncHistory(5);
        logger.info(`📊 Found ${syncHistory.length} recent sync operations`);

        if (syncHistory.length > 0) {
            logger.info('Latest sync operation:', {
                type: syncHistory[0].sync_type,
                date: syncHistory[0].sync_date,
                status: syncHistory[0].status,
                recordsProcessed: syncHistory[0].records_processed,
                duration: syncHistory[0].sync_duration_ms
            });
        }

        // Test 8: Test upcoming games query
        logger.info('8. Testing upcoming games query...');
        const upcomingGames = await dataStorageService.getUpcomingGames(7);
        logger.info(`📊 Found ${upcomingGames.length} upcoming games in next 7 days`);

        // Test 9: Test injured players query
        logger.info('9. Testing injured players query...');
        const injuredPlayers = await dataStorageService.getInjuredPlayers();
        logger.info(`📊 Found ${injuredPlayers.length} injured players`);

        logger.info('🎉 Supabase integration test completed successfully!');
        logger.info('📋 Summary:', {
            databaseConnected: true,
            activePlayersCount: activePlayers.length,
            upcomingGamesCount: upcomingGames.length,
            injuredPlayersCount: injuredPlayers.length,
            recentSyncsCount: syncHistory.length
        });

    } catch (error) {
        logger.error('❌ Supabase integration test failed:', error);
        process.exit(1);
    }
}

// Run the test
testSupabaseIntegration();
