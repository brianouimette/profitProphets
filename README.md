# NBA Fantasy Lineup Optimizer

A comprehensive NBA fantasy sports application that uses ML/AI to analyze player data, detect patterns, and optimize daily fantasy lineups.

## Features

- **Real-time Data Integration**: Fetches live NBA data from MySportsFeeds API
- **ML/AI Pattern Detection**: Identifies trends in player performance and team matchups
- **Lineup Optimization**: Builds optimal daily fantasy lineups within salary constraints
- **Injury Analysis**: Tracks player injuries and identifies replacement opportunities
- **Historical Analysis**: Provides comprehensive player and team statistics
- **Interactive Visualizations**: Charts and graphs for data analysis

## Tech Stack

- **Backend**: Node.js with Hono framework
- **Database**: Supabase (PostgreSQL)
- **Caching**: Upstash Redis
- **Background Jobs**: Inngest
- **Data Validation**: Zod
- **Testing**: Vitest
- **API Integration**: MySportsFeeds

## Setup

### Prerequisites

- Node.js 18+ 
- npm or yarn
- Supabase account
- Upstash Redis account (optional)
- MySportsFeeds API access

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd nba-fantasy-optimizer
```

2. Install dependencies:
```bash
npm install
```

3. Set up environment variables:
```bash
cp env.example .env
```

4. Configure your `.env` file with the required values:
```env
# MySportsFeeds API Configuration
MYSPORTSFEEDS_API_KEY=your_api_key
MYSPORTSFEEDS_PASSWORD=your_password
MYSPORTSFEEDS_BASE_URL=https://api.mysportsfeeds.com/v2.1/pull/nba

# Supabase Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

# Upstash Redis Configuration (optional)
UPSTASH_REDIS_REST_URL=your_upstash_redis_url
UPSTASH_REDIS_REST_TOKEN=your_upstash_redis_token

# Application Configuration
NODE_ENV=development
PORT=3000
LOG_LEVEL=info
```

### Development

1. Start the development server:
```bash
npm run dev
```

2. Test the API integration:
```bash
npm run test:api
```

3. Run the test suite:
```bash
npm test
```

4. Run tests in watch mode:
```bash
npm run test:watch
```

### API Endpoints

- `GET /health` - Health check
- `GET /api/players` - Get all players
- `GET /api/players/:team` - Get players for specific team
- `GET /api/games/:date` - Get games for specific date (YYYY-MM-DD)
- `GET /api/injuries` - Get all player injuries
- `GET /api/dfs-projections/:date` - Get DFS projections for specific date

### Testing

The application includes comprehensive tests for:
- API integration with MySportsFeeds
- Data validation and error handling
- Service layer functionality
- Edge cases and error scenarios

Run tests with:
```bash
npm test
```

## Project Structure

```
src/
├── config/           # Configuration management
├── services/         # API clients and data services
│   ├── dataFetchers/ # Individual data fetchers
│   └── MySportsFeedsClient.ts
├── types/            # TypeScript type definitions
├── utils/            # Utility functions
├── tests/            # Test files
├── cli/              # CLI tools
└── index.ts          # Main application entry point
```

## Current Status

**Milestone 1: API Integration & Data Pipeline** - ✅ In Progress
- [x] Project structure setup
- [x] MySportsFeeds API client implementation
- [x] Data fetchers for all endpoints
- [x] Error handling and retry logic
- [x] Basic test suite
- [x] CLI testing tool
- [ ] Supabase integration
- [ ] Comprehensive error handling
- [ ] Data validation improvements

## Next Steps

1. **Complete Milestone 1**: Finish Supabase integration and comprehensive error handling
2. **Milestone 2**: Design and implement database schema
3. **Milestone 3**: Build ML/AI components for pattern detection
4. **Milestone 4**: Create core application features
5. **Milestone 5**: Develop user interface

## Contributing

1. Follow the existing code style
2. Write tests for new features
3. Update documentation as needed
4. Ensure all tests pass before submitting

## License

MIT License - see LICENSE file for details
