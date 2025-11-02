import { MySportsFeedsClient } from '../MySportsFeedsClient';
import { GameLineupApiResponse } from '../../types/api-schemas';
import { logger } from '../../utils/logger';

export class GameLineupFetcher {
    constructor(private apiClient: MySportsFeedsClient) { }

    async fetchLineupForGame(season: string, gameId: number): Promise<GameLineupApiResponse> {
        try {
            logger.info(`Fetching lineup for game ${gameId}`, { season, gameId });

            const response = await this.apiClient.getGameLineup(season, gameId);

            logger.info(`Successfully fetched lineup for game ${gameId}`);

            return response;
        } catch (error) {
            logger.error(`Failed to fetch lineup for game ${gameId}:`, error);
            throw error;
        }
    }

    async fetchLineupsForGames(season: string, gameIds: number[]): Promise<GameLineupApiResponse[]> {
        const results: GameLineupApiResponse[] = [];

        // Filter out invalid game IDs
        const validGameIds = gameIds.filter(id => id !== undefined && id !== null && !isNaN(Number(id)));

        if (validGameIds.length === 0) {
            logger.warn('No valid game IDs provided for lineup fetching');
            return [];
        }

        for (const gameId of validGameIds) {
            try {
                const lineup = await this.fetchLineupForGame(season, gameId);
                results.push(lineup);

                // Add delay between requests
                await new Promise(resolve => setTimeout(resolve, 500));
            } catch (error) {
                logger.error(`Failed to fetch lineup for game ${gameId}:`, error);
                // Continue with other games even if one fails
            }
        }

        return results;
    }

    async fetchLineupByPosition(season: string, gameId: number, position: string): Promise<GameLineupApiResponse> {
        try {
            logger.info(`Fetching lineup for game ${gameId} by position ${position}`);

            const response = await this.apiClient.getGameLineup(season, gameId, {
                position: position
            });

            return response;
        } catch (error) {
            logger.error(`Failed to fetch lineup for game ${gameId} by position ${position}:`, error);
            throw error;
        }
    }

    async fetchLineupByType(season: string, gameId: number, lineupType: string): Promise<GameLineupApiResponse> {
        try {
            logger.info(`Fetching lineup for game ${gameId} by type ${lineupType}`);

            const response = await this.apiClient.getGameLineup(season, gameId, {
                lineupType: lineupType
            });

            return response;
        } catch (error) {
            logger.error(`Failed to fetch lineup for game ${gameId} by type ${lineupType}:`, error);
            throw error;
        }
    }

    async fetchAllLineupsForDate(season: string, date: string): Promise<GameLineupApiResponse[]> {
        try {
            // First get all games for the date
            const gamesResponse = await this.apiClient.getDailyGames(season, date);

            if (!gamesResponse.games || gamesResponse.games.length === 0) {
                logger.warn(`No games found for ${date}, cannot fetch lineups`);
                return [];
            }

            const gameIds = gamesResponse.games
                .map((game: any) => game.id)
                .filter((id: any) => id !== undefined && id !== null && !isNaN(Number(id)));
            
            if (gameIds.length === 0) {
                logger.warn(`No valid game IDs found for ${date}, cannot fetch lineups`);
                return [];
            }
            
            logger.info(`Found ${gameIds.length} valid games for ${date}, fetching lineups`);

            return await this.fetchLineupsForGames(season, gameIds);
        } catch (error) {
            logger.error(`Failed to fetch all lineups for ${date}:`, error);
            throw error;
        }
    }
}
