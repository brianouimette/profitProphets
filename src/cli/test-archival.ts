#!/usr/bin/env tsx

import { validateConfig } from '../config';
import { heatwaveDataArchivalService } from '../services/HeatWaveDataArchivalService';
// Remove unused import
import { logger } from '../utils/logger';

async function testArchivalSystem() {
    try {
        // Validate configuration
        validateConfig();
        logger.info('Configuration validated successfully');

        logger.info('🧪 Testing Data Archival System...');
        logger.info('=====================================');

        // Test 1: Get current season and archival status
        logger.info('\n📊 Getting archival status...');
        const status = await heatwaveDataArchivalService.getArchivalStatus();

        logger.info('Archive tables status:');

        for (const table of status) {
            logger.info(`  ${table.tableName}: ${table.totalRecords} records`);
            if (table.oldestRecord) {
                logger.info(`    Oldest: ${table.oldestRecord.toISOString()}`);
            }
            if (table.newestRecord) {
                logger.info(`    Newest: ${table.newestRecord.toISOString()}`);
            }
        }

        // Test 2: Test individual archival functions (dry run)
        logger.info('\n🔄 Testing individual archival functions...');

        const testSeason = 2023; // Test with previous season

        logger.info(`Testing archival for season ${testSeason}...`);

        // Test players archival
        logger.info('Testing players archival...');
        const playersResult = await heatwaveDataArchivalService.archivePlayers(testSeason);
        logger.info(`Players archival result: ${JSON.stringify(playersResult, null, 2)}`);

        // Test teams archival
        logger.info('Testing teams archival...');
        const teamsResult = await heatwaveDataArchivalService.archiveTeams(testSeason);
        logger.info(`Teams archival result: ${JSON.stringify(teamsResult, null, 2)}`);

        // Test games archival
        logger.info('Testing games archival...');
        const gamesResult = await heatwaveDataArchivalService.archiveGames(testSeason);
        logger.info(`Games archival result: ${JSON.stringify(gamesResult, null, 2)}`);

        // Test 3: Test rolling archival
        logger.info('\n📈 Testing rolling archival...');
        const rollingResults = await heatwaveDataArchivalService.archiveSeason(testSeason);

        logger.info('Rolling archival results:');
        Object.entries(rollingResults).forEach(([key, result]: [string, any]) => {
            logger.info(`  ${key}: ${result.archived} records archived, ${result.errors} errors`);
            if (result.error) {
                logger.error(`    Error: ${result.error}`);
            }
        });

        // Test 4: Test annual archival
        logger.info('\n🗓️ Testing annual archival...');
        const annualResults = await heatwaveDataArchivalService.archiveSeason(testSeason);

        logger.info('Annual archival results:');
        Object.entries(annualResults).forEach(([key, result]: [string, any]) => {
            logger.info(`  ${key}: ${result.archived} records archived, ${result.errors} errors`);
            if (result.error) {
                logger.error(`    Error: ${result.error}`);
            }
        });

        // Test 5: Test HeatWave database queries
        logger.info('\n🔍 Testing HeatWave database queries...');

        try {
            const { heatwaveService } = await import('../services/HeatWaveClient');
            const samplePlayers = await heatwaveService.query(
                'SELECT id, first_name, last_name FROM players LIMIT 5'
            );

            if (samplePlayers.length > 0) {
                logger.info('Sample players from HeatWave:');
                samplePlayers.forEach((player: any) => {
                    logger.info(`  ${player.first_name} ${player.last_name} (ID: ${player.id})`);
                });
            } else {
                logger.info('No players found in database');
            }
        } catch (error) {
            logger.error('Error testing HeatWave queries:', error);
        }

        // Test 6: Final status check
        logger.info('\n📊 Final archival status...');
        const finalStatus = await heatwaveDataArchivalService.getArchivalStatus();

        logger.info('Updated archive tables status:');
        for (const table of finalStatus) {
            logger.info(`  ${table.tableName}: ${table.totalRecords} records`);
        }

        logger.info('\n✅ Archival system test completed successfully!');

    } catch (error) {
        logger.error('❌ Archival system test failed:', error);
        process.exit(1);
    }
}

// Run the test
testArchivalSystem();

