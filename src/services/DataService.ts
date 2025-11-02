import { MySportsFeedsClient } from './MySportsFeedsClient';
import { DailyGamesFetcher } from './dataFetchers/DailyGamesFetcher';
import { PlayerGameLogsFetcher } from './dataFetchers/PlayerGameLogsFetcher';
import { GameLineupFetcher } from './dataFetchers/GameLineupFetcher';
import { InjuriesFetcher } from './dataFetchers/InjuriesFetcher';
import { PlayersFetcher } from './dataFetchers/PlayersFetcher';
import { DfsFetcher } from './dataFetchers/DfsFetcher';
import {
    GamesApiResponse,
    PlayersApiResponse,
    InjuriesApiResponse,
    DfsProjectionsApiResponse,
    DailyDfsDataApiResponse,
    PlayerGameLogsApiResponse,
    GameLineupApiResponse
} from '../types/api-schemas';
import { logger } from '../utils/logger';

export class DataService {
    private apiClient: MySportsFeedsClient;
    private dailyGamesFetcher: DailyGamesFetcher;
    private playerGameLogsFetcher: PlayerGameLogsFetcher;
    private gameLineupFetcher: GameLineupFetcher;
    private injuriesFetcher: InjuriesFetcher;
    private playersFetcher: PlayersFetcher;
    private dfsFetcher: DfsFetcher;

    constructor(apiClient: MySportsFeedsClient) {
        this.apiClient = apiClient;
        this.dailyGamesFetcher = new DailyGamesFetcher(apiClient);
        this.playerGameLogsFetcher = new PlayerGameLogsFetcher(apiClient);
        this.gameLineupFetcher = new GameLineupFetcher(apiClient);
        this.injuriesFetcher = new InjuriesFetcher(apiClient);
        this.playersFetcher = new PlayersFetcher(apiClient);
        this.dfsFetcher = new DfsFetcher(apiClient);
    }

    // Health check
    async healthCheck(): Promise<boolean> {
        try {
            return await this.apiClient.healthCheck();
        } catch (error) {
            logger.error('Data service health check failed:', error);
            return false;
        }
    }

    // Daily Games
    async getDailyGames(season: string, date: string): Promise<GamesApiResponse> {
        return this.dailyGamesFetcher.fetchGamesForDate(season, date);
    }

    async getUpcomingGames(season: string, daysAhead: number = 2): Promise<GamesApiResponse[]> {
        return this.dailyGamesFetcher.fetchUpcomingGames(season, daysAhead);
    }

    async getGamesForDateRange(season: string, startDate: string, endDate: string): Promise<GamesApiResponse[]> {
        return this.dailyGamesFetcher.fetchGamesForDateRange(season, startDate, endDate);
    }

    // Player Game Logs
    async getPlayerGameLogs(season: string, date: string): Promise<PlayerGameLogsApiResponse> {
        return this.playerGameLogsFetcher.fetchGameLogsForDate(season, date);
    }

    async getPlayerGameLogsForDateRange(season: string, startDate: string, endDate: string): Promise<PlayerGameLogsApiResponse[]> {
        return this.playerGameLogsFetcher.fetchGameLogsForDateRange(season, startDate, endDate);
    }

    async getPlayerGameLogsForPlayer(season: string, date: string, playerId: number): Promise<PlayerGameLogsApiResponse> {
        return this.playerGameLogsFetcher.fetchGameLogsForPlayer(season, date, playerId);
    }

    // Game Lineups
    async getGameLineup(season: string, gameId: number): Promise<GameLineupApiResponse> {
        return this.gameLineupFetcher.fetchLineupForGame(season, gameId);
    }

    async getAllLineupsForDate(season: string, date: string): Promise<GameLineupApiResponse[]> {
        return this.gameLineupFetcher.fetchAllLineupsForDate(season, date);
    }

    // Injuries
    async getAllInjuries(): Promise<InjuriesApiResponse> {
        return this.injuriesFetcher.fetchAllInjuries();
    }

    async getInjuriesForTeam(teamAbbreviation: string): Promise<InjuriesApiResponse> {
        return this.injuriesFetcher.fetchInjuriesForTeam(teamAbbreviation);
    }

    async getInjuriesForPlayer(playerId: number): Promise<InjuriesApiResponse> {
        return this.injuriesFetcher.fetchInjuriesForPlayer(playerId);
    }

    // Players
    async getAllPlayers(): Promise<PlayersApiResponse> {
        return this.playersFetcher.fetchAllPlayers();
    }

    async getAllPlayersPaginated(): Promise<PlayersApiResponse> {
        return this.playersFetcher.fetchAllPlayersPaginated();
    }

    async getPlayersForTeam(teamAbbreviation: string): Promise<PlayersApiResponse> {
        return this.playersFetcher.fetchPlayersForTeam(teamAbbreviation);
    }

    async getPlayerById(playerId: number): Promise<PlayersApiResponse> {
        return this.playersFetcher.fetchPlayerById(playerId);
    }

    // DFS Data
    async getDfsProjections(season: string, date: string): Promise<DfsProjectionsApiResponse> {
        return this.dfsFetcher.fetchDfsProjectionsForDate(season, date);
    }

    async getDailyDfs(season: string, date: string): Promise<DailyDfsDataApiResponse> {
        return this.dfsFetcher.fetchDailyDfsForDate(season, date);
    }

    async getDfsProjectionsForDateRange(season: string, startDate: string, endDate: string): Promise<DfsProjectionsApiResponse[]> {
        return this.dfsFetcher.fetchDfsProjectionsForDateRange(season, startDate, endDate);
    }

    async getDailyDfsForDateRange(season: string, startDate: string, endDate: string): Promise<DailyDfsDataApiResponse[]> {
        return this.dfsFetcher.fetchDailyDfsForDateRange(season, startDate, endDate);
    }

    // Comprehensive data fetching for a specific date
    async getCompleteDataForDate(season: string, date: string): Promise<{
        games: GamesApiResponse;
        playerGameLogs: PlayerGameLogsApiResponse;
        lineups: GameLineupApiResponse[];
        injuries: InjuriesApiResponse;
        dfsProjections: DfsProjectionsApiResponse;
        dailyDfs: DailyDfsDataApiResponse;
    }> {
        logger.info(`Fetching complete data for ${date}`);

        try {
            const [games, playerGameLogs, lineups, injuries, dfsProjections, dailyDfs] = await Promise.allSettled([
                this.getDailyGames(season, date),
                this.getPlayerGameLogs(season, date),
                this.getAllLineupsForDate(season, date),
                this.getAllInjuries(),
                this.getDfsProjections(season, date),
                this.getDailyDfs(season, date),
            ]);

            const result = {
                games: games.status === 'fulfilled' ? games.value : { games: [] },
                playerGameLogs: playerGameLogs.status === 'fulfilled' ? playerGameLogs.value : { playergamelogs: [] },
                lineups: lineups.status === 'fulfilled' ? lineups.value : [],
                injuries: injuries.status === 'fulfilled' ? injuries.value : { players: [] },
                dfsProjections: dfsProjections.status === 'fulfilled' ? dfsProjections.value : { dfsProjections: [] },
                dailyDfs: dailyDfs.status === 'fulfilled' ? dailyDfs.value : { dailydfsdata: [] },
            };

            logger.info(`Successfully fetched complete data for ${date}`);
            return result;
        } catch (error) {
            logger.error(`Failed to fetch complete data for ${date}:`, error);
            throw error;
        }
    }

    // Get current season (this would need to be updated based on actual season logic)
    getCurrentSeason(): string {
        const now = new Date();
        const year = now.getFullYear();
        const month = now.getMonth() + 1; // 0-based

        // NBA season typically starts in October
        if (month >= 10) {
            return `${year}-${(year + 1).toString().slice(-2)}`;
        } else {
            return `${year - 1}-${year.toString().slice(-2)}`;
        }
    }

    // Get today's date in YYYYMMDD format (MySportsFeeds API requirement)
    getTodayDateString(): string {
        return new Date().toISOString().split('T')[0].replace(/-/g, '');
    }

    // Get yesterday's date in YYYYMMDD format (MySportsFeeds API requirement)
    getYesterdayDateString(): string {
        const yesterday = new Date();
        yesterday.setDate(yesterday.getDate() - 1);
        return yesterday.toISOString().split('T')[0].replace(/-/g, '');
    }
}
