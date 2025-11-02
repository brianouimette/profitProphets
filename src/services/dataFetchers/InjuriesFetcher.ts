import { MySportsFeedsClient } from '../MySportsFeedsClient';
import { InjuriesApiResponse } from '../../types/api-schemas';
import { logger } from '../../utils/logger';

export class InjuriesFetcher {
    constructor(private apiClient: MySportsFeedsClient) { }

    async fetchAllInjuries(): Promise<InjuriesApiResponse> {
        try {
            logger.info('Fetching all player injuries');

            const response = await this.apiClient.getPlayerInjuries();

            if (response.players && response.players.length > 0) {
                logger.info(`Successfully fetched ${response.players.length} injury records`);
            } else {
                logger.warn('No injury records found');
            }

            return response;
        } catch (error) {
            logger.error('Failed to fetch all injuries:', error);
            throw error;
        }
    }

    async fetchInjuriesForPlayer(playerId: number): Promise<InjuriesApiResponse> {
        try {
            logger.info(`Fetching injuries for player ${playerId}`);

            const response = await this.apiClient.getPlayerInjuries({
                player: playerId.toString()
            });

            return response;
        } catch (error) {
            logger.error(`Failed to fetch injuries for player ${playerId}:`, error);
            throw error;
        }
    }

    async fetchInjuriesForTeam(teamAbbreviation: string): Promise<InjuriesApiResponse> {
        try {
            logger.info(`Fetching injuries for team ${teamAbbreviation}`);

            const response = await this.apiClient.getPlayerInjuries({
                team: teamAbbreviation
            });

            return response;
        } catch (error) {
            logger.error(`Failed to fetch injuries for team ${teamAbbreviation}:`, error);
            throw error;
        }
    }

    async fetchInjuriesForPosition(position: string): Promise<InjuriesApiResponse> {
        try {
            logger.info(`Fetching injuries for position ${position}`);

            const response = await this.apiClient.getPlayerInjuries({
                position: position
            });

            return response;
        } catch (error) {
            logger.error(`Failed to fetch injuries for position ${position}:`, error);
            throw error;
        }
    }

    async fetchInjuriesForPlayers(playerIds: number[]): Promise<InjuriesApiResponse> {
        try {
            logger.info(`Fetching injuries for ${playerIds.length} players`);

            const response = await this.apiClient.getPlayerInjuries({
                player: playerIds.map(id => id.toString())
            });

            return response;
        } catch (error) {
            logger.error(`Failed to fetch injuries for players:`, error);
            throw error;
        }
    }

    async fetchInjuriesForTeams(teamAbbreviations: string[]): Promise<InjuriesApiResponse> {
        try {
            logger.info(`Fetching injuries for ${teamAbbreviations.length} teams`);

            const response = await this.apiClient.getPlayerInjuries({
                team: teamAbbreviations
            });

            return response;
        } catch (error) {
            logger.error(`Failed to fetch injuries for teams:`, error);
            throw error;
        }
    }

    async fetchInjuriesByStatus(status: string): Promise<InjuriesApiResponse> {
        try {
            logger.info(`Fetching injuries with status ${status}`);

            // Note: The API might not support status filtering directly
            // This would need to be filtered client-side
            const response = await this.apiClient.getPlayerInjuries();

            // Filter by status if the API doesn't support it
            if (response.players) {
                response.players = response.players.filter((player: any) =>
                    player.currentInjury && player.currentInjury.status.toLowerCase() === status.toLowerCase()
                );
            }

            return response;
        } catch (error) {
            logger.error(`Failed to fetch injuries by status ${status}:`, error);
            throw error;
        }
    }
}
