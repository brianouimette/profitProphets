# Supabase Database Setup

This directory contains the database schema and setup instructions for the NBA Fantasy Optimizer.

## Database Schema

The `schema.sql` file contains the complete database schema with:

- **Players table**: NBA player information with positions, stats, and team affiliations
- **Teams table**: NBA team information with logos and social media
- **Venues table**: Arena and stadium information
- **Games table**: Game schedules and results
- **Player injuries table**: Current injury status and return dates
- **Player game logs table**: Historical performance statistics
- **DFS projections table**: Fantasy projections from multiple sources
- **Daily DFS data table**: Actual DFS performance data
- **Game lineups table**: Starting lineups and rotations
- **Data sync logs table**: Tracking of data synchronization operations

## Setup Instructions

### 1. Create Supabase Project

1. Go to [supabase.com](https://supabase.com) and create a new project
2. Note down your project URL and API keys

### 2. Set Environment Variables

Add these to your `.env` file:

```env
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
```

### 3. Run Database Schema

1. Go to your Supabase project dashboard
2. Navigate to the SQL Editor
3. Copy and paste the contents of `schema.sql`
4. Run the SQL to create all tables, indexes, and views

### 4. Test Connection

Run the Supabase integration test:

```bash
npm run test:supabase
```

This will:
- Test database connection
- Verify all tables exist
- Sync a small sample of players data
- Test database queries
- Show sync history

## Database Features

### Views

- **active_players**: All currently rostered players with team info
- **upcoming_games**: Games scheduled for the next 7 days with team details
- **injured_players**: Players with current injuries and their status

### Indexes

Optimized indexes for common queries:
- Player lookups by team and position
- Game queries by date and season
- Performance data by player and date
- DFS data by date and source

### Triggers

Automatic `updated_at` timestamp updates on all tables.

## API Endpoints

Once set up, you can use these endpoints:

### Database Status
- `GET /api/db/status` - Get sync status and health
- `GET /api/db/players` - Get active players from database
- `GET /api/db/games/upcoming?days=7` - Get upcoming games
- `GET /api/db/injuries` - Get injured players

### Data Sync
- `POST /api/sync/players` - Sync all players data
- `POST /api/sync/games/2025-01-15` - Sync games for specific date
- `POST /api/sync/injuries` - Sync injuries data
- `POST /api/sync/today` - Full sync for today

## Data Flow

1. **API Data** → **Transformers** → **Database Storage**
2. **Database Queries** → **API Responses**
3. **Sync Logging** → **Monitoring & Debugging**

## Monitoring

Check sync status and history:

```bash
curl http://localhost:3000/api/db/status
```

View recent sync operations and their success/failure rates.
