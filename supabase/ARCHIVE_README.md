# NBA Fantasy Optimizer - Data Archival System

## Overview

The data archival system manages historical NBA data to optimize database performance while preserving long-term data for ML/AI analysis. The system implements a hybrid approach:

- **Annual Archival**: Players, teams, and games are archived yearly
- **Rolling Archival**: Stats, injuries, and DFS data keep current + previous year, archive older data

## Architecture

### Archive Tables

All archive tables include:
- `season_year`: The NBA season the data applies to
- `archived_at`: When the record was moved to archive
- Same structure as main tables for seamless querying

### Annual Archive Tables
- `archive_players` - Complete player records by season
- `archive_teams` - Team information by season  
- `archive_games` - Game schedules and results by season

### Rolling Archive Tables
- `archive_player_game_logs` - Player statistics by season
- `archive_player_injuries` - Injury records by season
- `archive_dfs_projections` - DFS projections by season
- `archive_daily_dfs_data` - Daily DFS data by season

## Unified Views

The system provides unified views that combine current and archived data:

- `v_all_players` - All players (current + archived)
- `v_all_teams` - All teams (current + archived)
- `v_all_games` - All games (current + archived)
- `v_all_player_game_logs` - All player stats (current + archived)
- `v_all_player_injuries` - All injuries (current + archived)
- `v_all_dfs_projections` - All DFS projections (current + archived)
- `v_all_daily_dfs_data` - All daily DFS data (current + archived)

Each view includes a `data_source` field indicating 'current' or 'archived'.

## Setup

### 1. Run Archive Schema

```bash
# In Supabase SQL Editor, run:
supabase/archive-schema.sql
```

### 2. Test the System

```bash
npm run test:archival
```

## Usage

### Data Archival Service

```typescript
import { dataArchivalService } from './services/DataArchivalService';

// Archive a specific season
const results = await dataArchivalService.performAnnualArchival(2023);

// Archive rolling data
const rollingResults = await dataArchivalService.performRollingArchival(2023);

// Get archival status
const status = await dataArchivalService.getArchivalStatus();
```

### Querying Archived Data

```sql
-- Get all players from a specific season
SELECT * FROM v_all_players 
WHERE season_year = 2023;

-- Get player stats across multiple seasons
SELECT p.first_name, p.last_name, s.stats, s.season_year
FROM v_all_players p
JOIN v_all_player_game_logs s ON p.id = s.player_id
WHERE p.id = 12345
ORDER BY s.season_year DESC;

-- Get injury history for ML analysis
SELECT p.first_name, p.last_name, i.injury_type, i.injury_status, i.season_year
FROM v_all_players p
JOIN v_all_player_injuries i ON p.id = i.player_id
WHERE i.season_year >= 2020
ORDER BY i.season_year DESC;
```

## ML/AI Benefits

### Long-term Trend Analysis
- Access to multiple seasons of data
- Player performance trends over time
- Injury pattern analysis
- Team performance evolution

### Efficient Queries
- Indexed archive tables for fast retrieval
- Unified views for seamless data access
- Optimized for analytical workloads

### Data Integrity
- Preserved historical accuracy
- Consistent data structure
- Audit trail with archival timestamps

## Configuration

The archival service can be configured:

```typescript
const config: ArchivalConfig = {
    archivePlayersAfterYears: 1,    // Archive players after 1 year
    archiveTeamsAfterYears: 1,      // Archive teams after 1 year
    archiveGamesAfterYears: 1,       // Archive games after 1 year
    archiveStatsAfterYears: 1,       // Archive stats after 1 year
    archiveInjuriesAfterYears: 1,    // Archive injuries after 1 year
    archiveDfsDataAfterYears: 1      // Archive DFS data after 1 year
};
```

## Monitoring

### Check Archive Status
```typescript
const status = await dataArchivalService.getArchivalStatus();
console.log(`Current season: ${status.currentSeason}`);
console.log(`Archive tables: ${status.archiveTables.length}`);
```

### Archive Statistics
```sql
-- Get archive table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE tablename LIKE 'archive_%'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

## Maintenance

### Regular Archival
- Run annual archival at season end
- Run rolling archival monthly
- Monitor archive table sizes
- Clean up old archive data if needed

### Performance Optimization
- Archive tables are indexed for fast queries
- Views provide efficient data access
- Consider partitioning for very large archives

## Troubleshooting

### Common Issues

1. **Archive tables not found**: Run `archive-schema.sql` in Supabase
2. **Permission errors**: Ensure service role has archive table access
3. **Large archive operations**: Consider batching for large datasets

### Debug Commands

```bash
# Test archival system
npm run test:archival

# Check database connection
npm run test:supabase

# Test API integration
npm run test:api
```

