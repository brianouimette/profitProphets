import { PlayerData, TeamData, GameData, InjuryData, GameLogData, DfsProjectionData } from './DataStorageService';

export class DataTransformers {
    /**
     * Transform MySportsFeeds players data to database format
     */
    static transformPlayers(apiData: any): { players: PlayerData[]; teams: TeamData[] } {
        const players: PlayerData[] = [];
        // const teams: TeamData[] = []; // Not used in this function
        const teamMap = new Map<number, TeamData>();

        if (apiData.players && Array.isArray(apiData.players)) {
            for (const playerWrapper of apiData.players) {
                const player = playerWrapper.player || playerWrapper;

                // Transform player data
                const playerData: PlayerData = {
                    id: player.id,
                    first_name: player.firstName,
                    last_name: player.lastName,
                    primary_position: player.primaryPosition,
                    alternate_positions: player.alternatePositions || [],
                    jersey_number: player.jerseyNumber,
                    current_team_id: player.currentTeam?.id || null,
                    current_roster_status: player.currentRosterStatus,
                    height: player.height,
                    weight: player.weight,
                    birth_date: player.birthDate,
                    age: player.age,
                    birth_city: player.birthCity,
                    birth_country: player.birthCountry,
                    rookie: player.rookie || false,
                    high_school: player.highSchool,
                    college: player.college,
                    shoots: player.handedness?.shoots,
                    official_image_src: player.officialImageSrc,
                    social_media_accounts: player.socialMediaAccounts || [],
                    external_mappings: player.externalMappings || []
                };

                players.push(playerData);

                // Extract team data if present
                if (player.currentTeam && !teamMap.has(player.currentTeam.id)) {
                    const teamData: TeamData = {
                        id: player.currentTeam.id,
                        abbreviation: player.currentTeam.abbreviation,
                        city: player.currentTeam.city || '',
                        name: player.currentTeam.name || '',
                        conference: player.currentTeam.conference,
                        division: player.currentTeam.division
                    };
                    teamMap.set(player.currentTeam.id, teamData);
                }
            }
        }

        return {
            players,
            teams: Array.from(teamMap.values())
        };
    }

    /**
     * Transform MySportsFeeds games data to database format
     */
    static transformGames(apiData: any): { games: GameData[]; teams: TeamData[]; venues: any[] } {
        const games: GameData[] = [];
        // const teams: TeamData[] = []; // Not used in this function
        // const venues: any[] = []; // Not used in this function
        const teamMap = new Map<number, TeamData>();
        const venueMap = new Map<number, any>();

        if (apiData.games && Array.isArray(apiData.games)) {
            for (const game of apiData.games) {
                // The API returns games with nested schedule and score objects
                const schedule = game.schedule || {};
                const score = game.score || {};

                // Extract season from startTime (format: YYYY-MM-DDTHH:mm:ssZ)
                // NBA season typically spans from October to June
                let season: string | null = null;
                if (schedule.startTime) {
                    const date = new Date(schedule.startTime);
                    const year = date.getFullYear();
                    const month = date.getMonth() + 1; // 0-based
                    // If month is Oct-Dec (10-12), season is YYYY-YY+1, otherwise YYYY-1-YY
                    if (month >= 10) {
                        season = `${year}-${String(year + 1).slice(-2)}`;
                    } else {
                        season = `${year - 1}-${String(year).slice(-2)}`;
                    }
                }

                // Transform game data - use correct nested structure matching MySQL schema
                const gameData: GameData = {
                    id: schedule.id,
                    game_date: schedule.startTime ? schedule.startTime.split('T')[0] : null, // Extract date from startTime
                    away_team_id: schedule.awayTeam?.id ?? null,
                    home_team_id: schedule.homeTeam?.id ?? null,
                    status: schedule.playedStatus || schedule.scheduleStatus || null,
                    away_score: score.awayScoreTotal ?? null,
                    home_score: score.homeScoreTotal ?? null,
                    season: season,
                    game_type: 'REGULAR' // Default, could be enhanced to detect playoffs if needed
                };

                games.push(gameData);

                // Extract team data - use schedule.awayTeam and schedule.homeTeam
                if (schedule.awayTeam && !teamMap.has(schedule.awayTeam.id)) {
                    const teamData: TeamData = {
                        id: schedule.awayTeam.id,
                        abbreviation: schedule.awayTeam.abbreviation,
                        city: schedule.awayTeam.city || '',
                        name: schedule.awayTeam.name || '',
                        conference: schedule.awayTeam.conference,
                        division: schedule.awayTeam.division
                    };
                    teamMap.set(schedule.awayTeam.id, teamData);
                }

                if (schedule.homeTeam && !teamMap.has(schedule.homeTeam.id)) {
                    const teamData: TeamData = {
                        id: schedule.homeTeam.id,
                        abbreviation: schedule.homeTeam.abbreviation,
                        city: schedule.homeTeam.city || '',
                        name: schedule.homeTeam.name || '',
                        conference: schedule.homeTeam.conference,
                        division: schedule.homeTeam.division
                    };
                    teamMap.set(schedule.homeTeam.id, teamData);
                }

                // Extract venue data - use schedule.venue
                if (schedule.venue && !venueMap.has(schedule.venue.id)) {
                    const venueData = {
                        id: schedule.venue.id,
                        name: schedule.venue.name,
                        city: schedule.venue.city,
                        country: schedule.venue.country,
                        latitude: schedule.venue.geoCoordinates?.latitude,
                        longitude: schedule.venue.geoCoordinates?.longitude,
                        capacity: schedule.venue.capacitiesByEventType?.find((c: any) => c.eventType === 'BASKETBALL')?.capacity,
                        has_roof: schedule.venue.hasRoof,
                        has_retractable_roof: schedule.venue.hasRetractableRoof
                    };
                    venueMap.set(schedule.venue.id, venueData);
                }
            }
        }

        return {
            games,
            teams: Array.from(teamMap.values()),
            venues: Array.from(venueMap.values())
        };
    }

    /**
     * Transform MySportsFeeds injuries data to database format
     */
    static transformInjuries(apiData: any): InjuryData[] {
        const injuries: InjuryData[] = [];

        if (apiData.players && Array.isArray(apiData.players)) {
            for (const player of apiData.players) {
                if (player.currentInjury) {
                    const injuryData: InjuryData = {
                        id: player.currentInjury.id || Math.random() * 1000000, // Generate ID if not present
                        player_id: player.id,
                        injury_type: player.currentInjury.description || player.currentInjury.injuryType || null,
                        status: player.currentInjury.status || player.currentRosterStatus || 'ACTIVE',
                        start_date: player.currentInjury.injuryDate || null,
                        expected_return: player.currentInjury.expectedReturn || null,
                        description: player.currentInjury.description || null
                    };
                    injuries.push(injuryData);
                }
            }
        }

        return injuries;
    }

    /**
     * Transform MySportsFeeds player game logs to database format
     */
    static transformGameLogs(apiData: any): GameLogData[] {
        const gameLogs: GameLogData[] = [];

        if (apiData.playergamelogs && Array.isArray(apiData.playergamelogs)) {
            for (const log of apiData.playergamelogs) {
                const player = log.player;
                const game = log.game;
                const stats = log.stats;

                const gameLogData: GameLogData = {
                    // id is auto-increment, not needed for insert
                    player_id: player.id,
                    game_id: game.id,
                    minutes_played: stats?.Minutes?.value,
                    field_goals_made: stats?.FgM?.value,
                    field_goals_attempted: stats?.FgA?.value,
                    three_pointers_made: stats?.Fg3M?.value,
                    three_pointers_attempted: stats?.Fg3A?.value,
                    free_throws_made: stats?.FtM?.value,
                    free_throws_attempted: stats?.FtA?.value,
                    rebounds: stats?.Reb?.value,
                    assists: stats?.Ast?.value,
                    steals: stats?.Stl?.value,
                    blocks: stats?.Blk?.value,
                    turnovers: stats?.Tov?.value,
                    personal_fouls: stats?.Pf?.value,
                    plus_minus: stats?.PlusMinus?.value,
                    fantasy_points: stats?.FantasyPoints?.value
                };

                gameLogs.push(gameLogData);
            }
        }

        return gameLogs;
    }

    /**
     * Transform MySportsFeeds DFS projections to database format
     */
    static transformDfsProjections(apiData: any, _projectionDate: string): DfsProjectionData[] {
        const projections: DfsProjectionData[] = [];

        if (apiData.dfsprojections && Array.isArray(apiData.dfsprojections)) {
            for (const projection of apiData.dfsprojections) {
                const player = projection.player;
                const game = projection.game;
                const fantasyPoints = projection.fantasyPoints;

                if (fantasyPoints && Array.isArray(fantasyPoints)) {
                    for (const fp of fantasyPoints) {
                        const projectionData: DfsProjectionData = {
                            // id is auto-increment, not needed
                            player_id: player.id,
                            game_id: game.id,
                            salary: projection.salary ?? null,
                            projected_fantasy_points: fp.points ?? null,
                            ownership_percentage: projection.ownershipPercentage ?? null,
                            ceiling: null, // Not available in API
                            floor: null, // Not available in API
                            value_score: fp.points && projection.salary ? fp.points / (projection.salary / 1000) : null
                        };

                        projections.push(projectionData);
                    }
                }
            }
        }

        return projections;
    }

    /**
     * Transform MySportsFeeds daily DFS data to database format
     * Note: This returns DfsProjectionData for compatibility, but daily_dfs_data table structure is different
     */
    static transformDailyDfsData(apiData: any, _dfsDate: string): any[] {
        const dailyData: any[] = [];

        if (apiData.dailydfsdata && Array.isArray(apiData.dailydfsdata)) {
            for (const data of apiData.dailydfsdata) {
                const player = data.player;
                const game = data.game;
                const fantasyPoints = data.fantasyPoints;

                // Get fantasy points (actual, not projected)
                let fpValue = 0;
                if (fantasyPoints && Array.isArray(fantasyPoints) && fantasyPoints.length > 0) {
                    fpValue = parseFloat(fantasyPoints[0].points?.toString() || '0');
                }

                const dailyDataItem = {
                    // id is auto-increment, not needed
                    player_id: player.id,
                    game_id: game.id,
                    fantasy_points: fpValue || null,
                    salary: data.salary ?? null,
                    ownership_percentage: data.ownershipPercentage ?? null,
                    slate_id: null, // Not available in API response
                    platform: null // Not available in API response
                };

                dailyData.push(dailyDataItem);
            }
        }

        return dailyData;
    }
}
