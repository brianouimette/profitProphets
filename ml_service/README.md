# NBA Fantasy Optimizer ML Service

This Python service provides machine learning and statistical analysis capabilities for the NBA Fantasy Optimizer application.

## Features

- **Team Defense Analysis**: Analyze team defensive performance by position
- **Historical Data Analysis**: Process and analyze large historical datasets
- **Player Mapping**: Map between different data sources
- **Statistical Models**: Build and validate statistical models
- **REST API**: FastAPI-based service for integration with Node.js backend

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Variables

Create a `.env` file in the project root:

```env
# Supabase Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# ML Service Configuration
ML_API_HOST=0.0.0.0
ML_API_PORT=8001
MODEL_CACHE_DIR=./ml_models
HISTORICAL_DATA_PATH=./historical_data

# Performance Configuration
MAX_WORKERS=4
BATCH_SIZE=1000
```

### 3. Run the Service

```bash
# Development mode
python -m ml_service.api

# Production mode
uvicorn ml_service.api:app --host 0.0.0.0 --port 8001
```

## API Endpoints

### Health Check
- `GET /` - Basic health check
- `GET /health` - Detailed health check with database status

### Team Defense Analysis
- `GET /team-defense/stats` - Get team defense statistics
- `GET /team-defense/rankings` - Get defensive rankings by position
- `GET /team-defense/matchup/{player_id}/{opponent_team_id}` - Get matchup advantages
- `GET /team-defense/position-summary` - Get defensive performance summary by position

### Data Analysis
- `POST /analyze-historical-data` - Analyze historical data structure
- `GET /data-summary` - Get summary of available data

## Usage Examples

### Analyze Historical Data

```python
from ml_service.data_analyzer import analyze_historical_data

# Analyze your 4.66GB historical data
report = analyze_historical_data("/path/to/your/historical/data")
print(f"Data size: {report['data_structure']['total_size_gb']} GB")
```

### Team Defense Analysis

```python
from ml_service.team_defense_analyzer import TeamDefenseAnalyzer

analyzer = TeamDefenseAnalyzer()

# Get team defense stats
stats = analyzer.get_team_defense_stats()

# Get defensive rankings
rankings = analyzer.get_defensive_rankings(position="Guard")

# Get matchup advantages
advantages = analyzer.get_matchup_advantages(player_id=123, opponent_team_id=456)
```

### API Integration

```bash
# Get team defense stats
curl "http://localhost:8001/team-defense/stats?season=2024"

# Get defensive rankings for guards
curl "http://localhost:8001/team-defense/rankings?position=Guard"

# Get matchup advantages
curl "http://localhost:8001/team-defense/matchup/123/456"
```

## Development

### Project Structure

```
ml_service/
├── __init__.py
├── config.py              # Configuration management
├── database.py            # Database access layer
├── data_analyzer.py       # Historical data analysis
├── team_defense_analyzer.py  # Team defense analysis
├── api.py                 # FastAPI application
└── README.md              # This file
```

### Adding New Analyzers

1. Create a new analyzer class in a new file
2. Add the analyzer to the API endpoints
3. Update the main API module
4. Add tests for the new functionality

### Testing

```bash
# Run tests (when implemented)
python -m pytest tests/

# Run specific analyzer
python -m ml_service.team_defense_analyzer
```

## Integration with Node.js Backend

The ML service is designed to integrate seamlessly with the Node.js backend:

1. **Data Flow**: Node.js fetches data from MySportsFeeds → Supabase → Python ML Service
2. **API Communication**: Node.js makes HTTP requests to Python service
3. **Results**: Python returns analysis results to Node.js for display

### Example Node.js Integration

```javascript
// In your Node.js backend
const axios = require('axios');

async function getTeamDefenseStats(season) {
  try {
    const response = await axios.get(`http://localhost:8001/team-defense/stats?season=${season}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching team defense stats:', error);
    throw error;
  }
}
```

## Performance Considerations

- **Data Caching**: Results are cached to avoid repeated calculations
- **Batch Processing**: Large datasets are processed in batches
- **Memory Management**: Data is processed in chunks to manage memory usage
- **Async Processing**: Long-running analyses are handled asynchronously

## Troubleshooting

### Common Issues

1. **Database Connection**: Ensure Supabase credentials are correct
2. **Memory Issues**: Reduce batch size for large datasets
3. **API Timeouts**: Increase timeout settings for large analyses
4. **Data Quality**: Check data format and completeness

### Logs

The service logs all operations. Check the console output for detailed information about data processing and any errors.

## Future Enhancements

- [ ] Machine Learning Models (XGBoost, LightGBM)
- [ ] Advanced Statistical Analysis
- [ ] Real-time Data Processing
- [ ] Model Training and Validation
- [ ] Performance Optimization
- [ ] Additional Analysis Types
