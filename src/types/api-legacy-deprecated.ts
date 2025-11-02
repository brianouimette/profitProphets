/**
 * @deprecated This file contains legacy schemas that are no longer used.
 * All imports should use './api-schemas' instead.
 * This file will be removed in a future version.
 */

import { z } from 'zod';

// Re-export schemas from the new schemas file
export * from './api-schemas';

// Legacy Base API Response Schema (keeping for backward compatibility)
export const BaseApiResponseSchema = z.object({
    lastUpdatedOn: z.string().optional(),
    game: z.object({
        id: z.number(),
        date: z.string(),
        time: z.string(),
        awayTeam: z.object({
            id: z.number(),
            abbreviation: z.string(),
            city: z.string(),
            name: z.string(),
        }),
        homeTeam: z.object({
            id: z.number(),
            abbreviation: z.string(),
            city: z.string(),
            name: z.string(),
        }),
        venue: z.object({
            id: z.number(),
            name: z.string(),
            city: z.string(),
            state: z.string().optional(),
        }),
        gameStatus: z.string(),
        season: z.string(),
        week: z.number().optional(),
    }).optional(),
    games: z.array(z.object({
        id: z.number(),
        date: z.string(),
        time: z.string(),
        awayTeam: z.object({
            id: z.number(),
            abbreviation: z.string(),
            city: z.string(),
            name: z.string(),
        }),
        homeTeam: z.object({
            id: z.number(),
            abbreviation: z.string(),
            city: z.string(),
            name: z.string(),
        }),
        venue: z.object({
            id: z.number(),
            name: z.string(),
            city: z.string(),
            state: z.string().optional(),
        }),
        gameStatus: z.string(),
        season: z.string(),
        week: z.number().optional(),
    })).optional(),
    playerGameLogs: z.array(z.object({
        game: z.object({
            id: z.number(),
            date: z.string(),
            time: z.string(),
            awayTeam: z.object({
                id: z.number(),
                abbreviation: z.string(),
                city: z.string(),
                name: z.string(),
            }),
            homeTeam: z.object({
                id: z.number(),
                abbreviation: z.string(),
                city: z.string(),
                name: z.string(),
            }),
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
    players: z.array(z.object({
        player: z.object({
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
        }),
        teamAsOfDate: z.any().nullable().optional(),
    })).optional(),
    injuries: z.array(z.object({
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
        injury: z.object({
            type: z.string(),
            status: z.string(),
            description: z.string().optional(),
            lastUpdatedOn: z.string(),
        }),
    })).optional(),
    dfsProjections: z.array(z.object({
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
        game: z.object({
            id: z.number(),
            date: z.string(),
            time: z.string(),
            awayTeam: z.object({
                id: z.number(),
                abbreviation: z.string(),
                city: z.string(),
                name: z.string(),
            }),
            homeTeam: z.object({
                id: z.number(),
                abbreviation: z.string(),
                city: z.string(),
                name: z.string(),
            }),
        }),
        dfsType: z.string(),
        salary: z.number().optional(),
        projectedFantasyPoints: z.number().optional(),
        projectedStats: z.record(z.any()).optional(),
    })).optional(),
    dfs: z.array(z.object({
        slate: z.object({
            id: z.number(),
            name: z.string(),
            date: z.string(),
            time: z.string(),
            dfsType: z.string(),
        }),
        contest: z.object({
            id: z.number(),
            name: z.string(),
            entryFee: z.number(),
            totalPrizePool: z.number(),
            maxEntries: z.number(),
            maxEntriesPerUser: z.number(),
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
        salary: z.number(),
        fantasyPoints: z.number().optional(),
    })).optional(),
});

export type BaseApiResponse = z.infer<typeof BaseApiResponseSchema>;

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
