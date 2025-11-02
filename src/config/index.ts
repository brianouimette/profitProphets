import dotenv from 'dotenv';
import { ApiClientConfig } from '../types/api-schemas';

// Load environment variables
dotenv.config();

export const config = {
    // MySportsFeeds API Configuration
    mysportsfeeds: {
        apiKey: process.env.MYSPORTSFEEDS_API_KEY || '',
        password: process.env.MYSPORTSFEEDS_PASSWORD || '',
        baseUrl: process.env.MYSPORTSFEEDS_BASE_URL || 'https://api.mysportsfeeds.com/v2.1/pull/nba',
        rateLimitDelay: parseInt(process.env.API_RATE_LIMIT_DELAY || '1000'),
        maxRetryAttempts: parseInt(process.env.MAX_RETRY_ATTEMPTS || '3'),
        timeout: 30000, // 30 seconds
    } as ApiClientConfig,

    // MySQL HeatWave Configuration
    heatwave: {
        host: process.env.HEATWAVE_HOST || process.env.MYSQL_HOST || '',
        port: parseInt(process.env.HEATWAVE_PORT || process.env.MYSQL_PORT || '3306'),
        user: process.env.HEATWAVE_USER || process.env.MYSQL_USER || '',
        password: process.env.HEATWAVE_PASSWORD || process.env.MYSQL_PASSWORD || '',
        database: process.env.HEATWAVE_DATABASE || process.env.MYSQL_DATABASE || 'nba_fantasy',
    },

    // Upstash Redis Configuration
    redis: {
        url: process.env.UPSTASH_REDIS_REST_URL || '',
        token: process.env.UPSTASH_REDIS_REST_TOKEN || '',
    },

    // Inngest Configuration
    inngest: {
        eventKey: process.env.INNGEST_EVENT_KEY || '',
        signingKey: process.env.INNGEST_SIGNING_KEY || '',
    },

    // Application Configuration
    app: {
        nodeEnv: process.env.NODE_ENV || 'development',
        port: parseInt(process.env.PORT || '3000'),
        logLevel: process.env.LOG_LEVEL || 'info',
    },

    // Data Fetching Configuration
    data: {
        cacheTtlSeconds: parseInt(process.env.CACHE_TTL_SECONDS || '3600'),
        batchSize: 100,
        maxConcurrentRequests: 5,
    },
};

// Validation
export function validateConfig(): void {
    const requiredEnvVars = [
        'MYSPORTSFEEDS_API_KEY',
        'MYSPORTSFEEDS_PASSWORD',
        'HEATWAVE_HOST',
        'HEATWAVE_USER',
        'HEATWAVE_PASSWORD',
    ];

    const missingVars = requiredEnvVars.filter(varName => !process.env[varName]);

    if (missingVars.length > 0) {
        throw new Error(`Missing required environment variables: ${missingVars.join(', ')}`);
    }
}
