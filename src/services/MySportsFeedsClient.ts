import axios, { AxiosInstance, AxiosResponse } from 'axios';
import {
    BaseApiResponseSchema,
    ApiRequestParams,
    ApiError,
    ApiClientConfig,
    PlayersApiResponseSchema,
    InjuriesApiResponseSchema,
    GamesApiResponseSchema,
    PlayerGameLogsApiResponseSchema,
    GameLineupApiResponseSchema,
    DfsProjectionsApiResponseSchema,
    DailyDfsDataApiResponseSchema
} from '../types/api-schemas';
import { logger } from '../utils/logger';

export class MySportsFeedsClient {
    private client: AxiosInstance;
    private config: ApiClientConfig;

    constructor(config: ApiClientConfig) {
        this.config = config;

        // Create base64 encoded credentials
        const credentials = Buffer.from(`${config.apiKey}:${config.password}`).toString('base64');

        this.client = axios.create({
            baseURL: config.baseUrl,
            timeout: config.timeout,
            headers: {
                'Authorization': `Basic ${credentials}`,
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            },
        });

        // Add request interceptor for rate limiting
        this.client.interceptors.request.use(async (config) => {
            await this.delay(this.config.rateLimitDelay);
            return config;
        });

        // Add response interceptor for error handling
        this.client.interceptors.response.use(
            (response) => response,
            (error) => this.handleError(error)
        );
    }

    private async delay(ms: number): Promise<void> {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    private handleError(error: any): Promise<never> {
        const apiError: ApiError = {
            code: error.response?.status?.toString() || 'UNKNOWN',
            message: error.response?.data?.message || error.message || 'Unknown error occurred',
            details: error.response?.data,
        };

        logger.error('API Error:', apiError);
        return Promise.reject(apiError);
    }

    private async makeRequest<T>(
        endpoint: string,
        params: ApiRequestParams = {},
        retryCount = 0
    ): Promise<T> {
        const fullUrl = `${this.config.baseUrl}/${endpoint}`;
        const sanitizedParams = this.sanitizeParams(params);

        try {
            logger.info(`🚀 Making API request`, {
                method: 'GET',
                url: fullUrl,
                params: sanitizedParams,
                retryAttempt: retryCount + 1
            });

            const response: AxiosResponse<T> = await this.client.get(endpoint, {
                params: sanitizedParams,
            });

            logger.info(`✅ API request successful`, {
                url: fullUrl,
                status: response.status,
                statusText: response.statusText,
                headers: {
                    'content-type': response.headers['content-type'],
                    'content-length': response.headers['content-length']
                },
                dataType: Array.isArray(response.data) ? 'array' : typeof response.data,
                dataLength: Array.isArray(response.data) ? response.data.length : 'N/A',
                responseKeys: response.data && typeof response.data === 'object' ? Object.keys(response.data) : 'N/A'
            });

            // Log sample of response data for debugging
            if (response.data && typeof response.data === 'object') {
                const sampleData = this.getSampleData(response.data);
                logger.debug(`📊 Response data sample:`, sampleData);

                // Log the full raw response for schema debugging
                console.log('🔍 Full raw response:', JSON.stringify(response.data, null, 2));
            }

            return response.data;
        } catch (error: any) {
            logger.error(`❌ API request failed`, {
                url: fullUrl,
                params: sanitizedParams,
                retryAttempt: retryCount + 1,
                error: {
                    message: error.message,
                    code: error.code,
                    status: error.response?.status,
                    statusText: error.response?.statusText,
                    responseData: error.response?.data,
                    responseHeaders: error.response?.headers
                }
            });

            if (retryCount < this.config.maxRetryAttempts) {
                logger.warn(`🔄 Retrying API request... (${retryCount + 1}/${this.config.maxRetryAttempts})`, {
                    url: fullUrl,
                    nextRetryIn: Math.pow(2, retryCount) * 1000
                });

                // Exponential backoff
                await this.delay(Math.pow(2, retryCount) * 1000);
                return this.makeRequest<T>(endpoint, params, retryCount + 1);
            }

            throw error;
        }
    }

    private getSampleData(data: any, maxDepth = 2, currentDepth = 0): any {
        if (currentDepth >= maxDepth) {
            return '[Max depth reached]';
        }

        if (Array.isArray(data)) {
            return {
                type: 'array',
                length: data.length,
                sample: data.slice(0, 2).map(item => this.getSampleData(item, maxDepth, currentDepth + 1))
            };
        }

        if (data && typeof data === 'object') {
            const sample: any = {};
            const keys = Object.keys(data).slice(0, 5); // Show first 5 keys
            keys.forEach(key => {
                sample[key] = this.getSampleData(data[key], maxDepth, currentDepth + 1);
            });
            if (Object.keys(data).length > 5) {
                sample['...'] = `+${Object.keys(data).length - 5} more keys`;
            }
            return sample;
        }

        return data;
    }

    private sanitizeParams(params: ApiRequestParams): Record<string, any> {
        const sanitized: Record<string, any> = {};

        Object.entries(params).forEach(([key, value]) => {
            if (value !== undefined && value !== null) {
                if (Array.isArray(value)) {
                    sanitized[key] = value.join(',');
                } else {
                    sanitized[key] = value;
                }
            }
        });

        return sanitized;
    }

    // Daily Games
    async getDailyGames(season: string, date: string, params: ApiRequestParams = {}) {
        const endpoint = `${season}/date/${date}/games.json`;
        const data = await this.makeRequest(endpoint, params);
        return GamesApiResponseSchema.parse(data);
    }

    // Player Game Logs
    async getPlayerGameLogs(season: string, date: string, params: ApiRequestParams = {}) {
        const endpoint = `${season}/date/${date}/player_gamelogs.json`;
        const data = await this.makeRequest(endpoint, params);
        return PlayerGameLogsApiResponseSchema.parse(data);
    }

    // Game Lineup
    async getGameLineup(season: string, gameId: number, params: ApiRequestParams = {}) {
        const endpoint = `${season}/games/${gameId}/lineup.json`;
        const data = await this.makeRequest(endpoint, params);
        return GameLineupApiResponseSchema.parse(data);
    }

    // Player Injuries
    async getPlayerInjuries(params: ApiRequestParams = {}) {
        const endpoint = 'injuries.json';
        const data = await this.makeRequest(endpoint, params);
        return InjuriesApiResponseSchema.parse(data);
    }

    // Players
    async getPlayers(params: ApiRequestParams = {}) {
        const endpoint = 'players.json';
        const data = await this.makeRequest(endpoint, params);
        return PlayersApiResponseSchema.parse(data);
    }

    // Injury History
    async getInjuryHistory(params: ApiRequestParams = {}) {
        const endpoint = 'injury_history.json';
        const data = await this.makeRequest(endpoint, params);
        return BaseApiResponseSchema.parse(data);
    }

    // DFS Projections
    async getDfsProjections(season: string, date: string, params: ApiRequestParams = {}) {
        const endpoint = `${season}/date/${date}/dfs_projections.json`;
        const data = await this.makeRequest(endpoint, params);
        return DfsProjectionsApiResponseSchema.parse(data);
    }

    // Daily DFS
    async getDailyDfs(season: string, date: string, params: ApiRequestParams = {}) {
        const endpoint = `${season}/date/${date}/dfs.json`;
        const data = await this.makeRequest(endpoint, params);
        return DailyDfsDataApiResponseSchema.parse(data);
    }

    // Health check
    async healthCheck(): Promise<boolean> {
        try {
            await this.getPlayers({ limit: 1 });
            return true;
        } catch (error) {
            logger.error('Health check failed:', error);
            return false;
        }
    }
}
