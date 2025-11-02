import { MySportsFeedsClient } from '../MySportsFeedsClient';
import { GamesApiResponse } from '../../types/api-schemas';
import { logger } from '../../utils/logger';

export class DailyGamesFetcher {
    constructor(private apiClient: MySportsFeedsClient) { }

    async fetchGamesForDate(season: string, date: string): Promise<GamesApiResponse> {
        try {
            logger.info(`Fetching daily games for ${date}`, { season, date });

            const response = await this.apiClient.getDailyGames(season, date);

            if (response.games && response.games.length > 0) {
                logger.info(`Successfully fetched ${response.games.length} games for ${date}`);
            } else {
                logger.warn(`No games found for ${date}`);
            }

            return response;
        } catch (error) {
            logger.error(`Failed to fetch daily games for ${date}:`, error);
            throw error;
        }
    }

    async fetchGamesForDateRange(season: string, startDate: string, endDate: string): Promise<GamesApiResponse[]> {
        const results: GamesApiResponse[] = [];
        const currentDate = new Date(startDate);
        const endDateObj = new Date(endDate);

        while (currentDate <= endDateObj) {
            const dateStr = currentDate.toISOString().split('T')[0].replace(/-/g, '');

            try {
                const games = await this.fetchGamesForDate(season, dateStr);
                results.push(games);

                // Add delay between requests to respect rate limits
                await new Promise(resolve => setTimeout(resolve, 1000));
            } catch (error) {
                logger.error(`Failed to fetch games for ${dateStr}:`, error);
                // Continue with other dates even if one fails
            }

            currentDate.setDate(currentDate.getDate() + 1);
        }

        return results;
    }

    async fetchUpcomingGames(season: string, daysAhead: number = 2): Promise<GamesApiResponse[]> {
        const results: GamesApiResponse[] = [];
        const today = new Date();

        for (let i = 0; i < daysAhead; i++) {
            const futureDate = new Date(today);
            futureDate.setDate(today.getDate() + i);
            const dateStr = futureDate.toISOString().split('T')[0];

            try {
                const games = await this.fetchGamesForDate(season, dateStr);
                results.push(games);

                // Add delay between requests
                await new Promise(resolve => setTimeout(resolve, 1000));
            } catch (error) {
                logger.error(`Failed to fetch upcoming games for ${dateStr}:`, error);
            }
        }

        return results;
    }

    async fetchGamesByTeam(season: string, date: string, teamAbbreviation: string): Promise<GamesApiResponse> {
        try {
            logger.info(`Fetching games for team ${teamAbbreviation} on ${date}`);

            const response = await this.apiClient.getDailyGames(season, date, {
                team: teamAbbreviation
            });

            return response;
        } catch (error) {
            logger.error(`Failed to fetch games for team ${teamAbbreviation} on ${date}:`, error);
            throw error;
        }
    }

    async fetchGamesByStatus(season: string, date: string, status: string): Promise<GamesApiResponse> {
        try {
            logger.info(`Fetching games with status ${status} on ${date}`);

            const response = await this.apiClient.getDailyGames(season, date, {
                status: status
            });

            return response;
        } catch (error) {
            logger.error(`Failed to fetch games with status ${status} on ${date}:`, error);
            throw error;
        }
    }
}
