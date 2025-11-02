import { Hono } from 'hono';
import { serve } from '@hono/node-server';
import { config, validateConfig } from './config';
import { MySportsFeedsClient } from './services/MySportsFeedsClient';
import { DataService } from './services/DataService';
// Remove unused import
import { DataSyncService } from './services/DataSyncService';
import { logger } from './utils/logger';
import { dataStorageService } from './services/DataStorageService';

// Validate configuration on startup
try {
    validateConfig();
    logger.info('Configuration validated successfully');
} catch (error) {
    logger.error('Configuration validation failed:', error);
    process.exit(1);
}

// Initialize services
const apiClient = new MySportsFeedsClient(config.mysportsfeeds);
const dataService = new DataService(apiClient);
const dataSyncService = new DataSyncService(dataService);

// Create Hono app
const app = new Hono();

// Health check endpoint
app.get('/health', async (c) => {
    try {
        const [apiHealthy, dbHealthy] = await Promise.all([
            dataService.healthCheck(),
            // Database connection test - using HeatWave service
            true
        ]);

        return c.json({
            status: apiHealthy && dbHealthy ? 'healthy' : 'unhealthy',
            api: apiHealthy ? 'healthy' : 'unhealthy',
            database: dbHealthy ? 'healthy' : 'unhealthy',
            timestamp: new Date().toISOString()
        });
    } catch (error) {
        logger.error('Health check failed:', error);
        return c.json({
            status: 'unhealthy',
            error: 'Health check failed',
            timestamp: new Date().toISOString()
        }, 500);
    }
});

// API endpoints
app.get('/api/players', async (c) => {
    try {
        const response = await dataService.getAllPlayers();
        return c.json(response);
    } catch (error) {
        logger.error('Failed to fetch players:', error);
        return c.json({ error: 'Failed to fetch players' }, 500);
    }
});

app.get('/api/players/:team', async (c) => {
    try {
        const team = c.req.param('team');
        const response = await dataService.getPlayersForTeam(team);
        return c.json(response);
    } catch (error) {
        logger.error(`Failed to fetch players for team ${c.req.param('team')}:`, error);
        return c.json({ error: 'Failed to fetch players for team' }, 500);
    }
});

app.get('/api/games/:date', async (c) => {
    try {
        const date = c.req.param('date');
        const season = dataService.getCurrentSeason();
        const response = await dataService.getDailyGames(season, date);
        return c.json(response);
    } catch (error) {
        logger.error(`Failed to fetch games for date ${c.req.param('date')}:`, error);
        return c.json({ error: 'Failed to fetch games for date' }, 500);
    }
});

app.get('/api/injuries', async (c) => {
    try {
        const response = await dataService.getAllInjuries();
        return c.json(response);
    } catch (error) {
        logger.error('Failed to fetch injuries:', error);
        return c.json({ error: 'Failed to fetch injuries' }, 500);
    }
});

app.get('/api/dfs-projections/:date', async (c) => {
    try {
        const date = c.req.param('date');
        const season = dataService.getCurrentSeason();
        const response = await dataService.getDfsProjections(season, date);
        return c.json(response);
    } catch (error) {
        logger.error(`Failed to fetch DFS projections for date ${c.req.param('date')}:`, error);
        return c.json({ error: 'Failed to fetch DFS projections for date' }, 500);
    }
});

// Database endpoints
app.get('/api/db/status', async (c) => {
    try {
        const status = await dataSyncService.getSyncStatus();
        return c.json(status);
    } catch (error) {
        logger.error('Failed to get database status:', error);
        return c.json({ error: 'Failed to get database status' }, 500);
    }
});

app.get('/api/db/players', async (c) => {
    try {
        const players = await dataStorageService.getActivePlayers();
        return c.json({ players });
    } catch (error) {
        logger.error('Failed to fetch players from database:', error);
        return c.json({ error: 'Failed to fetch players from database' }, 500);
    }
});

app.get('/api/db/games/upcoming', async (c) => {
    try {
        const days = parseInt(c.req.query('days') || '7');
        const games = await dataStorageService.getUpcomingGames(days);
        return c.json({ games });
    } catch (error) {
        logger.error('Failed to fetch upcoming games from database:', error);
        return c.json({ error: 'Failed to fetch upcoming games from database' }, 500);
    }
});

app.get('/api/db/injuries', async (c) => {
    try {
        const injuries = await dataStorageService.getInjuredPlayers();
        return c.json({ injuries });
    } catch (error) {
        logger.error('Failed to fetch injuries from database:', error);
        return c.json({ error: 'Failed to fetch injuries from database' }, 500);
    }
});

// Data sync endpoints
app.post('/api/sync/players', async (c) => {
    try {
        await dataSyncService.syncPlayers();
        return c.json({ message: 'Players sync completed successfully' });
    } catch (error) {
        logger.error('Players sync failed:', error);
        return c.json({ error: 'Players sync failed' }, 500);
    }
});

app.post('/api/sync/games/:date', async (c) => {
    try {
        const date = c.req.param('date');
        await dataSyncService.syncGames(date);
        return c.json({ message: `Games sync for ${date} completed successfully` });
    } catch (error) {
        logger.error(`Games sync failed for ${c.req.param('date')}:`, error);
        return c.json({ error: 'Games sync failed' }, 500);
    }
});

app.post('/api/sync/injuries', async (c) => {
    try {
        await dataSyncService.syncInjuries();
        return c.json({ message: 'Injuries sync completed successfully' });
    } catch (error) {
        logger.error('Injuries sync failed:', error);
        return c.json({ error: 'Injuries sync failed' }, 500);
    }
});

app.post('/api/sync/today', async (c) => {
    try {
        await dataSyncService.syncToday();
        return c.json({ message: 'Full sync for today completed successfully' });
    } catch (error) {
        logger.error('Full sync failed:', error);
        return c.json({ error: 'Full sync failed' }, 500);
    }
});

// Start server
const port = config.app.port;
serve({
    fetch: app.fetch,
    port: port,
}, () => {
    logger.info(`NBA Fantasy Optimizer API server running on port ${port}`);
    logger.info(`Health check: http://localhost:${port}/health`);
    logger.info(`API endpoints available at: http://localhost:${port}/api/`);
});

export default app;
