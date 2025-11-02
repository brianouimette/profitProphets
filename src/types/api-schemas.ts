import { z } from 'zod';

// Base API Response Schema
export const BaseApiResponseSchema = z.object({
    lastUpdatedOn: z.string().optional(),
});

// Common schemas for reuse
export const TeamSchema = z.object({
    id: z.number(),
    abbreviation: z.string(),
    city: z.string().optional(),
    name: z.string().optional(),
});

export const VenueSchema = z.object({
    id: z.number(),
    name: z.string(),
    city: z.string().optional(),
    country: z.string().optional(),
    geoCoordinates: z.object({
        latitude: z.number(),
        longitude: z.number(),
    }).optional(),
    capacitiesByEventType: z.array(z.object({
        eventType: z.string(),
        capacity: z.number(),
    })).optional(),
    hasRoof: z.boolean().optional(),
    hasRetractableRoof: z.boolean().optional(),
});

export const PlayerSchema = z.object({
    id: z.number(),
    firstName: z.string(),
    lastName: z.string(),
    primaryPosition: z.string(),
    alternatePositions: z.array(z.string()).optional(),
    jerseyNumber: z.union([z.string(), z.number()]).nullable().optional(),
    currentTeam: z.object({
        id: z.number(),
        abbreviation: z.string(),
        city: z.string().optional(),
        name: z.string().optional(),
    }).nullable().optional(),
    currentRosterStatus: z.string().optional(),
    currentInjury: z.any().nullable().optional(),
    height: z.string().nullable().optional(),
    weight: z.number().nullable().optional(),
    birthDate: z.string().nullable().optional(),
    age: z.number().nullable().optional(),
    birthCity: z.string().nullable().optional(),
    birthCountry: z.string().nullable().optional(),
    rookie: z.boolean().optional(),
    highSchool: z.string().nullable().optional(),
    college: z.string().nullable().optional(),
    handedness: z.object({
        shoots: z.string().nullable().optional(),
    }).optional(),
    officialImageSrc: z.string().nullable().optional(),
    socialMediaAccounts: z.array(z.any()).optional(),
    currentContractYear: z.any().nullable().optional(),
    drafted: z.any().nullable().optional(),
    externalMappings: z.array(z.object({
        source: z.string(),
        id: z.union([z.string(), z.number()]),
    })).optional(),
});

// Players API Response Schema
export const PlayersApiResponseSchema = BaseApiResponseSchema.extend({
    players: z.array(z.object({
        player: PlayerSchema,
        teamAsOfDate: z.any().nullable().optional(),
    })).optional(),
    references: z.any().optional(),
});

// Games API Response Schema
export const GamesApiResponseSchema = BaseApiResponseSchema.extend({
    games: z.array(z.object({
        schedule: z.object({
            id: z.number(),
            startTime: z.string(),
            endedTime: z.string().nullable().optional(),
            awayTeam: TeamSchema,
            homeTeam: TeamSchema,
            venue: VenueSchema.optional(),
            venueAllegiance: z.string().optional(),
            scheduleStatus: z.string().optional(),
            originalStartTime: z.string().nullable().optional(),
            delayedOrPostponedReason: z.string().nullable().optional(),
            playedStatus: z.string().optional(),
            attendance: z.number().nullable().optional(),
            officials: z.array(z.object({
                id: z.number(),
                title: z.string(),
                firstName: z.string(),
                lastName: z.string(),
            })).optional(),
            broadcasters: z.array(z.string()).optional(),
            weather: z.object({
                type: z.string(),
                description: z.string(),
                wind: z.object({
                    speed: z.object({
                        milesPerHour: z.number(),
                        kilometersPerHour: z.number(),
                    }),
                    direction: z.object({
                        degrees: z.number(),
                        label: z.string(),
                    }),
                }),
                temperature: z.object({
                    fahrenheit: z.number(),
                    celsius: z.number(),
                }),
                precipitation: z.object({
                    type: z.string().nullable().optional(),
                    percent: z.number().nullable().optional(),
                    amount: z.object({
                        millimeters: z.number().nullable().optional(),
                        centimeters: z.number().nullable().optional(),
                        inches: z.number().nullable().optional(),
                        feet: z.number().nullable().optional(),
                    }).optional(),
                }).optional(),
                humidityPercent: z.number(),
            }).nullable().optional(),
        }),
        score: z.object({
            currentQuarter: z.number().nullable().optional(),
            currentQuarterSecondsRemaining: z.number().nullable().optional(),
            currentIntermission: z.number().nullable().optional(),
            awayScoreTotal: z.number().nullable().optional(),
            homeScoreTotal: z.number().nullable().optional(),
            quarters: z.array(z.object({
                quarterNumber: z.number(),
                awayScore: z.number(),
                homeScore: z.number(),
            })).optional(),
        }).optional(),
    })).optional(),
    references: z.object({
        teamReferences: z.array(TeamSchema.extend({
            homeVenue: VenueSchema.optional(),
            teamColoursHex: z.array(z.string()).optional(),
            socialMediaAccounts: z.array(z.any()).optional(),
            officialLogoImageSrc: z.string().optional(),
        })).optional(),
        venueReferences: z.array(VenueSchema).optional(),
    }).nullable().optional(),
});

// Injuries API Response Schema
export const InjuriesApiResponseSchema = BaseApiResponseSchema.extend({
    players: z.array(z.object({
        id: z.number(),
        firstName: z.string(),
        lastName: z.string(),
        primaryPosition: z.string(),
        jerseyNumber: z.union([z.string(), z.number()]).nullable().optional(),
        currentTeam: z.object({
            id: z.number(),
            abbreviation: z.string(),
        }).optional(),
        currentRosterStatus: z.string().optional(),
        currentInjury: z.object({
            description: z.string(),
            playingProbability: z.string(),
        }).optional(),
        height: z.string().nullable().optional(),
        weight: z.number().nullable().optional(),
        birthDate: z.string().nullable().optional(),
        age: z.number().nullable().optional(),
        birthCity: z.string().nullable().optional(),
        birthCountry: z.string().nullable().optional(),
        rookie: z.boolean().optional(),
        highSchool: z.string().nullable().optional(),
        college: z.string().nullable().optional(),
        handedness: z.object({
            shoots: z.string().nullable().optional(),
        }).optional(),
        officialImageSrc: z.string().nullable().optional(),
        socialMediaAccounts: z.array(z.any()).optional(),
    })).optional(),
});

// Player Game Logs API Response Schema
export const PlayerGameLogsApiResponseSchema = BaseApiResponseSchema.extend({
    playergamelogs: z.array(z.object({
        game: z.object({
            id: z.number(),
            date: z.string(),
            time: z.string(),
            awayTeam: TeamSchema,
            homeTeam: TeamSchema,
        }),
        player: z.object({
            id: z.number(),
            firstName: z.string(),
            lastName: z.string(),
            position: z.string(),
            jerseyNumber: z.number().optional(),
        }),
        team: z.object({
            id: z.number(),
            abbreviation: z.string(),
            city: z.string(),
            name: z.string(),
        }),
        stats: z.record(z.any()).optional(),
    })).optional(),
});

// DFS Projections API Response Schema
export const DfsProjectionsApiResponseSchema = BaseApiResponseSchema.extend({
    dfsProjections: z.array(z.object({
        player: z.object({
            id: z.number(),
            firstName: z.string(),
            lastName: z.string(),
            position: z.string(),
            jerseyNumber: z.union([z.string(), z.number()]).nullable().optional(),
        }),
        team: z.object({
            id: z.number(),
            abbreviation: z.string(),
        }),
        game: z.object({
            id: z.number(),
            startTime: z.string(),
            awayTeamAbbreviation: z.string(),
            homeTeamAbbreviation: z.string(),
        }),
        fantasyPoints: z.array(z.object({
            source: z.string(),
            points: z.number(),
        })).optional(),
        salary: z.number().optional(),
        ownershipPercentage: z.number().optional(),
    })).optional(),
    references: z.any().optional(),
});

// Daily DFS Data API Response Schema
export const DailyDfsDataApiResponseSchema = BaseApiResponseSchema.extend({
    dailydfsdata: z.array(z.object({
        player: z.object({
            id: z.number(),
            firstName: z.string(),
            lastName: z.string(),
            position: z.string(),
            jerseyNumber: z.number().optional(),
        }),
        team: z.object({
            id: z.number(),
            abbreviation: z.string(),
        }),
        game: z.object({
            id: z.number(),
            startTime: z.string(),
            awayTeamAbbreviation: z.string(),
            homeTeamAbbreviation: z.string(),
        }),
        fantasyPoints: z.array(z.object({
            source: z.string(),
            points: z.number(),
        })).optional(),
        salary: z.number().optional(),
        ownershipPercentage: z.number().optional(),
    })).optional(),
    references: z.any().optional(),
});

// Game Lineup API Response Schema
export const GameLineupApiResponseSchema = BaseApiResponseSchema.extend({
    lineup: z.object({
        game: z.object({
            id: z.number(),
            date: z.string(),
            time: z.string(),
            awayTeam: TeamSchema,
            homeTeam: TeamSchema,
        }),
        awayTeamLineup: z.array(z.object({
            player: z.object({
                id: z.number(),
                firstName: z.string(),
                lastName: z.string(),
                position: z.string(),
                jerseyNumber: z.number().optional(),
            }),
            position: z.string(),
            starter: z.boolean(),
        })).optional(),
        homeTeamLineup: z.array(z.object({
            player: z.object({
                id: z.number(),
                firstName: z.string(),
                lastName: z.string(),
                position: z.string(),
                jerseyNumber: z.number().optional(),
            }),
            position: z.string(),
            starter: z.boolean(),
        })).optional(),
    }).optional(),
});

// Type exports
export type PlayersApiResponse = z.infer<typeof PlayersApiResponseSchema>;
export type GamesApiResponse = z.infer<typeof GamesApiResponseSchema>;
export type InjuriesApiResponse = z.infer<typeof InjuriesApiResponseSchema>;
export type PlayerGameLogsApiResponse = z.infer<typeof PlayerGameLogsApiResponseSchema>;
export type DfsProjectionsApiResponse = z.infer<typeof DfsProjectionsApiResponseSchema>;
export type DailyDfsDataApiResponse = z.infer<typeof DailyDfsDataApiResponseSchema>;
export type GameLineupApiResponse = z.infer<typeof GameLineupApiResponseSchema>;

// API Request Parameters
export interface ApiRequestParams {
    team?: string | string[];
    status?: string | string[];
    sort?: string;
    offset?: number;
    limit?: number;
    force?: boolean;
    player?: string | string[];
    position?: string | string[];
    game?: string | string[];
    stats?: string | string[];
    lineupType?: string;
    season?: string;
    date?: string;
    rosterStatus?: string | string[];
    country?: string | string[];
    dfsType?: string | string[];
}

// API Error Response
export interface ApiError {
    code: string;
    message: string;
    details?: any;
}

// API Client Configuration
export interface ApiClientConfig {
    baseUrl: string;
    apiKey: string;
    password: string;
    rateLimitDelay: number;
    maxRetryAttempts: number;
    timeout: number;
}

