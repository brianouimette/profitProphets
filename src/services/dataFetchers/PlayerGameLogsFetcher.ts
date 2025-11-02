import { MySportsFeedsClient } from '../MySportsFeedsClient';
import { PlayerGameLogsApiResponse } from '../../types/api-schemas';
import { logger } from '../../utils/logger';

export class PlayerGameLogsFetcher {
    constructor(private apiClient: MySportsFeedsClient) { }

    async fetchGameLogsForDate(season: string, date: string): Promise<PlayerGameLogsApiResponse> {
        try {
            logger.info(`Fetching player game logs for ${date}`, { season, date });

            const response = await this.apiClient.getPlayerGameLogs(season, date);

            if (response.playergamelogs && response.playergamelogs.length > 0) {
                logger.info(`Successfully fetched ${response.playergamelogs.length} player game logs for ${date}`);
            } else {
                logger.warn(`No player game logs found for ${date}`);
            }

            return response;
        } catch (error) {
            logger.error(`Failed to fetch player game logs for ${date}:`, error);
            throw error;
        }
    }

    async fetchGameLogsForDateRange(season: string, startDate: string, endDate: string): Promise<PlayerGameLogsApiResponse[]> {
        const results: PlayerGameLogsApiResponse[] = [];
        const currentDate = new Date(startDate);
        const endDateObj = new Date(endDate);

        while (currentDate <= endDateObj) {
            const dateStr = currentDate.toISOString().split('T')[0].replace(/-/g, '');

            try {
                const gameLogs = await this.fetchGameLogsForDate(season, dateStr);
                results.push(gameLogs);

                // Add delay between requests
                await new Promise(resolve => setTimeout(resolve, 1000));
            } catch (error) {
                logger.error(`Failed to fetch game logs for ${dateStr}:`, error);
            }

            currentDate.setDate(currentDate.getDate() + 1);
        }

        return results;
    }

    async fetchGameLogsForPlayer(season: string, date: string, playerId: number): Promise<PlayerGameLogsApiResponse> {
        try {
            logger.info(`Fetching game logs for player ${playerId} on ${date}`);

            const response = await this.apiClient.getPlayerGameLogs(season, date, {
                player: playerId.toString()
            });

            return response;
        } catch (error) {
            logger.error(`Failed to fetch game logs for player ${playerId} on ${date}:`, error);
            throw error;
        }
    }

    async fetchGameLogsForTeam(season: string, date: string, teamAbbreviation: string): Promise<PlayerGameLogsApiResponse> {
        try {
            logger.info(`Fetching game logs for team ${teamAbbreviation} on ${date}`);

            const response = await this.apiClient.getPlayerGameLogs(season, date, {
                team: teamAbbreviation
            });

            return response;
        } catch (error) {
            logger.error(`Failed to fetch game logs for team ${teamAbbreviation} on ${date}:`, error);
            throw error;
        }
    }

    async fetchGameLogsForPosition(season: string, date: string, position: string): Promise<PlayerGameLogsApiResponse> {
        try {
            logger.info(`Fetching game logs for position ${position} on ${date}`);

            const response = await this.apiClient.getPlayerGameLogs(season, date, {
                position: position
            });

            return response;
        } catch (error) {
            logger.error(`Failed to fetch game logs for position ${position} on ${date}:`, error);
            throw error;
        }
    }

    async fetchGameLogsForGame(season: string, date: string, gameId: number): Promise<PlayerGameLogsApiResponse> {
        try {
            logger.info(`Fetching game logs for game ${gameId} on ${date}`);

            const response = await this.apiClient.getPlayerGameLogs(season, date, {
                game: gameId.toString()
            });

            return response;
        } catch (error) {
            logger.error(`Failed to fetch game logs for game ${gameId} on ${date}:`, error);
            throw error;
        }
    }

    async fetchGameLogsWithStats(season: string, date: string, stats: string[]): Promise<PlayerGameLogsApiResponse> {
        try {
            logger.info(`Fetching game logs with specific stats for ${date}`, { stats });

            const response = await this.apiClient.getPlayerGameLogs(season, date, {
                stats: stats
            });

            return response;
        } catch (error) {
            logger.error(`Failed to fetch game logs with stats for ${date}:`, error);
            throw error;
        }
    }
}
