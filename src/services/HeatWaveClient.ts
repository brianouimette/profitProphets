import mysql from 'mysql2/promise';
import { config } from '../config';
import { logger } from '../utils/logger';

export class HeatWaveService {
    private connection: mysql.Connection | null = null;
    private pool: mysql.Pool | null = null;
    private initialized: boolean = false;

    constructor() {
        // Don't auto-initialize - let caller control when to initialize
    }

    /**
     * Initialize the connection pool (call this after env vars are loaded)
     */
    async ensureInitialized(): Promise<void> {
        if (this.initialized && this.pool) {
            return;
        }
        await this.initializeConnection();
    }

    /**
     * Initialize MySQL HeatWave connection
     */
    private async initializeConnection(): Promise<void> {
        try {
            // Create connection pool for better performance
            // Oracle Cloud MySQL HeatWave requires SSL connections
            this.pool = mysql.createPool({
                host: config.heatwave.host,
                port: config.heatwave.port,
                user: config.heatwave.user,
                password: config.heatwave.password,
                database: config.heatwave.database,
                waitForConnections: true,
                connectionLimit: 10,
                queueLimit: 0,
                ssl: {
                    rejectUnauthorized: false // Oracle Cloud uses self-signed certificates
                }
            });

            // Test connection
            this.connection = await this.pool.getConnection();
            await this.connection.ping();
            this.connection.destroy();

            this.initialized = true;
            logger.info('HeatWave connection pool initialized');
        } catch (error) {
            logger.error('Failed to initialize HeatWave connection:', error);
            this.connection = null;
            this.pool = null;
            this.initialized = false;
        }
    }

    /**
     * Get a connection from the pool
     */
    async getConnection(): Promise<mysql.Connection> {
        await this.ensureInitialized();

        if (!this.pool) {
            throw new Error('HeatWave connection pool not initialized');
        }
        return await this.pool.getConnection();
    }

    /**
     * Execute a query with parameters
     */
    async query<T = any>(sql: string, params?: any[]): Promise<T[]> {
        await this.ensureInitialized();

        if (!this.pool) {
            throw new Error('HeatWave connection pool not initialized');
        }

        try {
            const [rows] = await this.pool.execute(sql, params);
            return rows as T[];
        } catch (error) {
            logger.error('HeatWave query error:', error);
            throw error;
        }
    }

    /**
     * Execute a single query and return the first result
     */
    async queryOne<T = any>(sql: string, params?: any[]): Promise<T | null> {
        const results = await this.query<T>(sql, params);
        return results.length > 0 ? results[0] : null;
    }

    /**
     * Test the database connection
     */
    async testConnection(): Promise<boolean> {
        try {
            await this.ensureInitialized();

            if (!this.pool) {
                logger.error('HeatWave connection pool not initialized');
                return false;
            }

            const connection = await this.getConnection();
            await connection.ping();
            connection.destroy();

            logger.info('HeatWave connection test successful');
            return true;
        } catch (error) {
            logger.error('HeatWave connection test error:', error);
            return false;
        }
    }

    /**
     * Get database health status
     */
    async getHealthStatus(): Promise<{
        connected: boolean;
        tables: string[];
        lastSync?: string;
    }> {
        try {
            if (!this.pool) {
                return { connected: false, tables: [] };
            }

            // Get list of tables
            const tables = await this.query<{ table_name: string }>(
                `SELECT table_name FROM information_schema.tables 
                 WHERE table_schema = ?`,
                [config.heatwave.database]
            );

            // Get last sync time
            const lastSync = await this.queryOne<{ created_at: string }>(
                'SELECT created_at FROM data_sync_logs ORDER BY created_at DESC LIMIT 1'
            );

            return {
                connected: true,
                tables: tables.map(t => t.table_name),
                ...(lastSync?.created_at && { lastSync: lastSync.created_at })
            };
        } catch (error) {
            logger.error('Failed to get health status:', error);
            return { connected: false, tables: [] };
        }
    }

    /**
     * Close all connections
     */
    async close(): Promise<void> {
        if (this.pool) {
            await this.pool.end();
            this.pool = null;
        }
        this.connection = null;
    }
}

// Export singleton instance (but allow for lazy initialization)
export const heatwaveService = new HeatWaveService();
