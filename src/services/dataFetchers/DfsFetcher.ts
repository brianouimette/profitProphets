import { MySportsFeedsClient } from '../MySportsFeedsClient';
import { DfsProjectionsApiResponse, DailyDfsDataApiResponse } from '../../types/api-schemas';
import { logger } from '../../utils/logger';

export class DfsFetcher {
    constructor(private apiClient: MySportsFeedsClient) { }

    // DFS Projections
    async fetchDfsProjectionsForDate(season: string, date: string): Promise<DfsProjectionsApiResponse> {
        try {
            logger.info(`Fetching DFS projections for ${date}`, { season, date });

            const response = await this.apiClient.getDfsProjections(season, date);

            if (response.dfsProjections && response.dfsProjections.length > 0) {
                logger.info(`Successfully fetched ${response.dfsProjections.length} DFS projections for ${date}`);
            } else {
                logger.warn(`No DFS projections found for ${date}`);
            }

            return response;
        } catch (error) {
            logger.error(`Failed to fetch DFS projections for ${date}:`, error);
            throw error;
        }
    }

    async fetchDfsProjectionsForDateRange(season: string, startDate: string, endDate: string): Promise<DfsProjectionsApiResponse[]> {
        const results: DfsProjectionsApiResponse[] = [];
        const currentDate = new Date(startDate);
        const endDateObj = new Date(endDate);

        while (currentDate <= endDateObj) {
            const dateStr = currentDate.toISOString().split('T')[0];

            try {
                const projections = await this.fetchDfsProjectionsForDate(season, dateStr);
                results.push(projections);

                // Add delay between requests
                await new Promise(resolve => setTimeout(resolve, 1000));
            } catch (error) {
                logger.error(`Failed to fetch DFS projections for ${dateStr}:`, error);
            }

            currentDate.setDate(currentDate.getDate() + 1);
        }

        return results;
    }

    async fetchDfsProjectionsForTeam(season: string, date: string, teamAbbreviation: string): Promise<DfsProjectionsApiResponse> {
        try {
            logger.info(`Fetching DFS projections for team ${teamAbbreviation} on ${date}`);

            const response = await this.apiClient.getDfsProjections(season, date, {
                team: teamAbbreviation
            });

            return response;
        } catch (error) {
            logger.error(`Failed to fetch DFS projections for team ${teamAbbreviation} on ${date}:`, error);
            throw error;
        }
    }

    async fetchDfsProjectionsForPlayer(season: string, date: string, playerId: number): Promise<DfsProjectionsApiResponse> {
        try {
            logger.info(`Fetching DFS projections for player ${playerId} on ${date}`);

            const response = await this.apiClient.getDfsProjections(season, date, {
                player: playerId.toString()
            });

            return response;
        } catch (error) {
            logger.error(`Failed to fetch DFS projections for player ${playerId} on ${date}:`, error);
            throw error;
        }
    }

    async fetchDfsProjectionsForPosition(season: string, date: string, position: string): Promise<DfsProjectionsApiResponse> {
        try {
            logger.info(`Fetching DFS projections for position ${position} on ${date}`);

            const response = await this.apiClient.getDfsProjections(season, date, {
                position: position
            });

            return response;
        } catch (error) {
            logger.error(`Failed to fetch DFS projections for position ${position} on ${date}:`, error);
            throw error;
        }
    }

    async fetchDfsProjectionsForDfsType(season: string, date: string, dfsType: string): Promise<DfsProjectionsApiResponse> {
        try {
            logger.info(`Fetching DFS projections for DFS type ${dfsType} on ${date}`);

            const response = await this.apiClient.getDfsProjections(season, date, {
                dfsType: dfsType
            });

            return response;
        } catch (error) {
            logger.error(`Failed to fetch DFS projections for DFS type ${dfsType} on ${date}:`, error);
            throw error;
        }
    }

    // Daily DFS
    async fetchDailyDfsForDate(season: string, date: string): Promise<DailyDfsDataApiResponse> {
        try {
            logger.info(`Fetching daily DFS data for ${date}`, { season, date });

            const response = await this.apiClient.getDailyDfs(season, date);

            if (response.dailydfsdata && response.dailydfsdata.length > 0) {
                logger.info(`Successfully fetched ${response.dailydfsdata.length} daily DFS records for ${date}`);
            } else {
                logger.warn(`No daily DFS data found for ${date}`);
            }

            return response;
        } catch (error) {
            logger.error(`Failed to fetch daily DFS data for ${date}:`, error);
            throw error;
        }
    }

    async fetchDailyDfsForDateRange(season: string, startDate: string, endDate: string): Promise<DailyDfsDataApiResponse[]> {
        const results: DailyDfsDataApiResponse[] = [];
        const currentDate = new Date(startDate);
        const endDateObj = new Date(endDate);

        while (currentDate <= endDateObj) {
            const dateStr = currentDate.toISOString().split('T')[0].replace(/-/g, '');

            try {
                const dailyDfs = await this.fetchDailyDfsForDate(season, dateStr);
                results.push(dailyDfs);

                // Add delay between requests
                await new Promise(resolve => setTimeout(resolve, 1000));
            } catch (error) {
                logger.error(`Failed to fetch daily DFS data for ${dateStr}:`, error);
            }

            currentDate.setDate(currentDate.getDate() + 1);
        }

        return results;
    }

    async fetchDailyDfsForTeam(season: string, date: string, teamAbbreviation: string): Promise<DailyDfsDataApiResponse> {
        try {
            logger.info(`Fetching daily DFS data for team ${teamAbbreviation} on ${date}`);

            const response = await this.apiClient.getDailyDfs(season, date, {
                team: teamAbbreviation
            });

            return response;
        } catch (error) {
            logger.error(`Failed to fetch daily DFS data for team ${teamAbbreviation} on ${date}:`, error);
            throw error;
        }
    }

    async fetchDailyDfsForPlayer(season: string, date: string, playerId: number): Promise<DailyDfsDataApiResponse> {
        try {
            logger.info(`Fetching daily DFS data for player ${playerId} on ${date}`);

            const response = await this.apiClient.getDailyDfs(season, date, {
                player: playerId.toString()
            });

            return response;
        } catch (error) {
            logger.error(`Failed to fetch daily DFS data for player ${playerId} on ${date}:`, error);
            throw error;
        }
    }

    async fetchDailyDfsForPosition(season: string, date: string, position: string): Promise<DailyDfsDataApiResponse> {
        try {
            logger.info(`Fetching daily DFS data for position ${position} on ${date}`);

            const response = await this.apiClient.getDailyDfs(season, date, {
                position: position
            });

            return response;
        } catch (error) {
            logger.error(`Failed to fetch daily DFS data for position ${position} on ${date}:`, error);
            throw error;
        }
    }

    async fetchDailyDfsForDfsType(season: string, date: string, dfsType: string): Promise<DailyDfsDataApiResponse> {
        try {
            logger.info(`Fetching daily DFS data for DFS type ${dfsType} on ${date}`);

            const response = await this.apiClient.getDailyDfs(season, date, {
                dfsType: dfsType
            });

            return response;
        } catch (error) {
            logger.error(`Failed to fetch daily DFS data for DFS type ${dfsType} on ${date}:`, error);
            throw error;
        }
    }

    async fetchDailyDfsForSlate(season: string, date: string, slateId: number): Promise<DailyDfsDataApiResponse> {
        try {
            logger.info(`Fetching daily DFS data for slate ${slateId} on ${date}`);

            // First get all DFS data for the date, then filter by slate
            const response = await this.fetchDailyDfsForDate(season, date);

            // Note: Slate filtering is not supported by the current API schema
            // The response will contain all DFS data for the date

            return response;
        } catch (error) {
            logger.error(`Failed to fetch daily DFS data for slate ${slateId} on ${date}:`, error);
            throw error;
        }
    }
}
