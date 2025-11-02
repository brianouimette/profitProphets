import { MySportsFeedsClient } from '../MySportsFeedsClient';
import { PlayersApiResponse } from '../../types/api-schemas';
import { logger } from '../../utils/logger';

export class PlayersFetcher {
    constructor(private apiClient: MySportsFeedsClient) { }

    async fetchAllPlayers(): Promise<PlayersApiResponse> {
        try {
            logger.info('Fetching all players');

            const response = await this.apiClient.getPlayers();

            if (response.players && response.players.length > 0) {
                logger.info(`Successfully fetched ${response.players.length} players`);
            } else {
                logger.warn('No players found');
            }

            return response;
        } catch (error) {
            logger.error('Failed to fetch all players:', error);
            throw error;
        }
    }

    async fetchPlayersForSeason(season: string): Promise<PlayersApiResponse> {
        try {
            logger.info(`Fetching players for season ${season}`);

            const response = await this.apiClient.getPlayers({
                season: season
            });

            return response;
        } catch (error) {
            logger.error(`Failed to fetch players for season ${season}:`, error);
            throw error;
        }
    }

    async fetchPlayersForTeam(teamAbbreviation: string): Promise<PlayersApiResponse> {
        try {
            logger.info(`Fetching players for team ${teamAbbreviation}`);

            const response = await this.apiClient.getPlayers({
                team: teamAbbreviation
            });

            return response;
        } catch (error) {
            logger.error(`Failed to fetch players for team ${teamAbbreviation}:`, error);
            throw error;
        }
    }

    async fetchPlayersForPosition(position: string): Promise<PlayersApiResponse> {
        try {
            logger.info(`Fetching players for position ${position}`);

            const response = await this.apiClient.getPlayers({
                position: position
            });

            return response;
        } catch (error) {
            logger.error(`Failed to fetch players for position ${position}:`, error);
            throw error;
        }
    }

    async fetchPlayerById(playerId: number): Promise<PlayersApiResponse> {
        try {
            logger.info(`Fetching player ${playerId}`);

            const response = await this.apiClient.getPlayers({
                player: playerId.toString()
            });

            return response;
        } catch (error) {
            logger.error(`Failed to fetch player ${playerId}:`, error);
            throw error;
        }
    }

    async fetchPlayersByRosterStatus(rosterStatus: string): Promise<PlayersApiResponse> {
        try {
            logger.info(`Fetching players with roster status ${rosterStatus}`);

            const response = await this.apiClient.getPlayers({
                rosterStatus: rosterStatus
            });

            return response;
        } catch (error) {
            logger.error(`Failed to fetch players with roster status ${rosterStatus}:`, error);
            throw error;
        }
    }

    async fetchPlayersByCountry(country: string): Promise<PlayersApiResponse> {
        try {
            logger.info(`Fetching players from country ${country}`);

            const response = await this.apiClient.getPlayers({
                country: country
            });

            return response;
        } catch (error) {
            logger.error(`Failed to fetch players from country ${country}:`, error);
            throw error;
        }
    }

    async fetchPlayersForDate(date: string): Promise<PlayersApiResponse> {
        try {
            logger.info(`Fetching players for date ${date}`);

            const response = await this.apiClient.getPlayers({
                date: date
            });

            return response;
        } catch (error) {
            logger.error(`Failed to fetch players for date ${date}:`, error);
            throw error;
        }
    }

    async fetchPlayersWithPagination(offset: number = 0, limit: number = 100): Promise<PlayersApiResponse> {
        try {
            logger.info(`Fetching players with pagination (offset: ${offset}, limit: ${limit})`);

            const response = await this.apiClient.getPlayers({
                offset: offset,
                limit: limit
            });

            return response;
        } catch (error) {
            logger.error(`Failed to fetch players with pagination:`, error);
            throw error;
        }
    }

    async fetchAllPlayersPaginated(): Promise<PlayersApiResponse> {
        const allPlayers: any[] = [];
        let offset = 0;
        const limit = 100;
        let hasMore = true;

        try {
            while (hasMore) {
                logger.info(`Fetching players batch (offset: ${offset})`);

                const response = await this.fetchPlayersWithPagination(offset, limit);

                if (response.players && response.players.length > 0) {
                    allPlayers.push(...response.players);
                    offset += limit;

                    // If we got fewer players than the limit, we've reached the end
                    if (response.players.length < limit) {
                        hasMore = false;
                    }
                } else {
                    hasMore = false;
                }

                // Add delay between requests
                await new Promise(resolve => setTimeout(resolve, 1000));
            }

            logger.info(`Successfully fetched ${allPlayers.length} total players`);

            return {
                players: allPlayers,
                lastUpdatedOn: new Date().toISOString()
            };
        } catch (error) {
            logger.error('Failed to fetch all players with pagination:', error);
            throw error;
        }
    }
}
