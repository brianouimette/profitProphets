"""
ML Service API
FastAPI service for ML model endpoints
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Dict, Any, List
import pandas as pd
import numpy as np
from ml_service.config import config
from ml_service.team_defense_analyzer import TeamDefenseAnalyzer
from ml_service.data_analyzer import HistoricalDataAnalyzer
from ml_service.enhanced_data_analyzer import EnhancedDataAnalyzer
from ml_service.database import MLDatabase
from ml_service.simulation_engine import SimulationEngine, PlayerProjection
from ml_service.ml_model_trainer import MLModelTrainer
from ml_service.advanced_analytics import AdvancedAnalytics
from ml_service.value_analyzer import ValueAnalyzer
from ml_service.injury_impact_analyzer import InjuryImpactAnalyzer
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="NBA Fantasy Optimizer ML Service",
    description="Machine Learning service for NBA fantasy sports analysis",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize analyzers
team_defense_analyzer = TeamDefenseAnalyzer()
value_analyzer = ValueAnalyzer()
injury_analyzer = InjuryImpactAnalyzer()
db = MLDatabase()
simulation_engine = SimulationEngine(db)
ml_trainer = MLModelTrainer(db, config)
advanced_analytics = AdvancedAnalytics(db)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "NBA Fantasy Optimizer ML Service", "status": "healthy"}

@app.get("/health")
async def health_check():
    """Detailed health check"""
    try:
        # Test database connection
        from ml_service.database import db
        players_count = len(db.get_players(limit=1))
        
        return {
            "status": "healthy",
            "database_connected": players_count >= 0,
            "service": "ml_service",
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/team-defense/stats")
async def get_team_defense_stats(
    season: Optional[str] = Query(None, description="NBA season to analyze"),
    position: Optional[str] = Query(None, description="Position to filter by")
):
    """Get team defense statistics"""
    try:
        results = team_defense_analyzer.get_team_defense_stats(season)
        
        if results.empty:
            return {"message": "No data available", "data": []}
        
        # Filter by position if specified
        if position:
            results = results[results['position'] == position]
        
        return {
            "message": "Team defense stats retrieved successfully",
            "count": len(results),
            "data": results.to_dict('records')
        }
    except Exception as e:
        logger.error(f"Error getting team defense stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/team-defense/rankings")
async def get_defensive_rankings(
    position: Optional[str] = Query(None, description="Position to rank by")
):
    """Get defensive rankings by position"""
    try:
        results = team_defense_analyzer.get_defensive_rankings(position)
        
        if results.empty:
            return {"message": "No rankings available", "data": []}
        
        return {
            "message": "Defensive rankings retrieved successfully",
            "count": len(results),
            "data": results.to_dict('records')
        }
    except Exception as e:
        logger.error(f"Error getting defensive rankings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/team-defense/matchup/{player_id}/{opponent_team_id}")
async def get_matchup_advantage(
    player_id: int,
    opponent_team_id: int
):
    """Get matchup advantages for a specific player against a team"""
    try:
        advantages = team_defense_analyzer.get_matchup_advantages(player_id, opponent_team_id)
        
        if not advantages:
            return {"message": "No matchup data available", "data": {}}
        
        return {
            "message": "Matchup advantages calculated successfully",
            "player_id": player_id,
            "opponent_team_id": opponent_team_id,
            "data": advantages
        }
    except Exception as e:
        logger.error(f"Error calculating matchup advantages: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/team-defense/position-summary")
async def get_position_defense_summary():
    """Get defensive performance summary by position"""
    try:
        results = team_defense_analyzer.get_position_defense_summary()
        
        if results.empty:
            return {"message": "No position summary available", "data": []}
        
        return {
            "message": "Position defense summary retrieved successfully",
            "count": len(results),
            "data": results.to_dict('records')
        }
    except Exception as e:
        logger.error(f"Error getting position defense summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze-historical-data")
async def analyze_historical_data_endpoint(
    data_path: str = Query(..., description="Path to historical data directory")
):
    """Analyze historical data structure and quality"""
    try:
        analyzer = HistoricalDataAnalyzer(data_path)
        report = analyzer.generate_data_quality_report()
        
        return {
            "message": "Historical data analysis completed",
            "data_path": data_path,
            "report": report
        }
    except Exception as e:
        logger.error(f"Error analyzing historical data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/data-summary")
async def get_data_summary():
    """Get summary of available data in the database"""
    try:
        from ml_service.database import db
        summary = db.get_historical_data_summary()
        
        return {
            "message": "Data summary retrieved successfully",
            "data": summary
        }
    except Exception as e:
        logger.error(f"Error getting data summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/enhanced/player-mapping")
async def create_player_mapping(
    api_key: str = Query(..., description="MySportsFeeds API key"),
    season: str = Query("latest", description="NBA season to analyze")
):
    """Create player mapping between historical and MySportsFeeds data"""
    try:
        db = MLDatabase()
        analyzer = EnhancedDataAnalyzer(db)
        
        # Fetch MySportsFeeds data
        if not analyzer.fetch_mysportsfeeds_data(api_key, season):
            raise HTTPException(status_code=500, detail="Failed to fetch MySportsFeeds data")
        
        # Create player mapping
        if not analyzer.create_player_mapping():
            raise HTTPException(status_code=500, detail="Failed to create player mapping")
        
        # Get mapping summary
        summary = analyzer.get_mapping_summary()
        
        # Save mapping table
        analyzer.save_mapping_table()
        
        return {
            "message": "Player mapping created successfully",
            "season": season,
            "mapping_summary": summary,
            "mapping_file": "enhanced_player_mapping.csv"
        }
    except Exception as e:
        logger.error(f"Error creating player mapping: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/enhanced/team-defense")
async def get_enhanced_team_defense(
    season_year: Optional[int] = Query(None, description="Season year to analyze")
):
    """Get enhanced team defense analysis with player mapping"""
    try:
        db = MLDatabase()
        analyzer = EnhancedDataAnalyzer(db)
        
        # Analyze team defense
        defense_analysis = analyzer.analyze_team_defense_with_mapping(season_year)
        
        if defense_analysis.empty:
            return {"message": "No team defense data available", "data": []}
        
        return {
            "message": "Enhanced team defense analysis completed",
            "season_year": season_year,
            "count": len(defense_analysis),
            "data": defense_analysis.to_dict('records')
        }
    except Exception as e:
        logger.error(f"Error getting enhanced team defense: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/enhanced/player-trends/{player_id}")
async def get_player_trends(
    player_id: str,
    days_back: int = Query(30, description="Number of days to look back")
):
    """Get player performance trends"""
    try:
        analyzer = EnhancedDataAnalyzer(db)
        
        # Get player trends
        trends = analyzer.get_player_performance_trends(player_id, days_back)
        
        if not trends:
            return {"message": "No performance data available", "data": {}}
        
        return {
            "message": "Player performance trends retrieved successfully",
            "player_id": player_id,
            "days_back": days_back,
            "data": trends
        }
    except Exception as e:
        logger.error(f"Error getting player trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== SIMULATION ENGINE ENDPOINTS =====

@app.post("/simulation/monte-carlo")
async def run_monte_carlo_simulation(
    lineup: List[Dict[str, Any]],
    iterations: int = Query(10000, description="Number of simulation iterations"),
    include_correlations: bool = Query(True, description="Include player correlations")
):
    """Run Monte Carlo simulation for lineup optimization"""
    try:
        # Convert lineup to PlayerProjection objects
        player_projections = []
        for player in lineup:
            projection = PlayerProjection(
                player_id=player['player_id'],
                name=player.get('name', ''),
                position=player.get('position', ''),
                salary=player.get('salary', 0),
                mean_projection=player.get('mean_projection', 0),
                std_projection=player.get('std_projection', 1),
                distribution_type=player.get('distribution_type', 'normal'),
                correlation_factors=player.get('correlation_factors', {})
            )
            player_projections.append(projection)
        
        # Run simulation
        result = simulation_engine.monte_carlo_simulation(
            player_projections, 
            iterations, 
            include_correlations=include_correlations
        )
        
        return {
            "message": "Monte Carlo simulation completed successfully",
            "iterations": iterations,
            "result": {
                "mean_score": result.mean_score,
                "std_score": result.std_score,
                "percentiles": {
                    "p10": result.percentile_10,
                    "p25": result.percentile_25,
                    "p50": result.percentile_50,
                    "p75": result.percentile_75,
                    "p90": result.percentile_90
                },
                "confidence_interval_95": result.confidence_interval_95,
                "probability_above_threshold": result.probability_above_threshold
            }
        }
    except Exception as e:
        logger.error(f"Error in Monte Carlo simulation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/simulation/scenario-analysis")
async def run_scenario_analysis(
    base_lineup: List[Dict[str, Any]],
    scenarios: List[Dict[str, Any]],
    iterations: int = Query(5000, description="Number of iterations per scenario")
):
    """Run scenario analysis for what-if analysis"""
    try:
        # Convert lineup to PlayerProjection objects
        player_projections = []
        for player in base_lineup:
            projection = PlayerProjection(
                player_id=player['player_id'],
                name=player.get('name', ''),
                position=player.get('position', ''),
                salary=player.get('salary', 0),
                mean_projection=player.get('mean_projection', 0),
                std_projection=player.get('std_projection', 1),
                distribution_type=player.get('distribution_type', 'normal'),
                correlation_factors=player.get('correlation_factors', {})
            )
            player_projections.append(projection)
        
        # Run scenario analysis
        results = simulation_engine.scenario_analysis(
            player_projections, 
            scenarios, 
            iterations
        )
        
        return {
            "message": "Scenario analysis completed successfully",
            "scenarios": len(scenarios),
            "iterations_per_scenario": iterations,
            "results": {name: {
                "mean_score": result.mean_score,
                "std_score": result.std_score,
                "percentile_50": result.percentile_50,
                "confidence_interval_95": result.confidence_interval_95
            } for name, result in results.items()}
        }
    except Exception as e:
        logger.error(f"Error in scenario analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== ML MODEL ENDPOINTS =====

@app.post("/ml/train-fantasy-points-model")
async def train_fantasy_points_model(
    start_date: str = Query(..., description="Training data start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="Training data end date (YYYY-MM-DD)"),
    model_type: str = Query("random_forest", description="Model type to train"),
    test_size: float = Query(0.2, description="Test set size (0.0-1.0)")
):
    """Train fantasy points prediction model"""
    try:
        # Prepare training data
        X, y = ml_trainer.prepare_training_data(start_date, end_date)
        
        if X.empty or y.empty:
            raise HTTPException(status_code=400, detail="No training data available")
        
        # Train model
        results = ml_trainer.train_fantasy_points_model(X, y, test_size, model_type)
        
        if 'error' in results:
            raise HTTPException(status_code=500, detail=results['error'])
        
        return {
            "message": "Fantasy points model training completed",
            "model_type": model_type,
            "training_period": f"{start_date} to {end_date}",
            "results": results
        }
    except Exception as e:
        logger.error(f"Error training fantasy points model: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ml/train-value-model")
async def train_value_model(
    start_date: str = Query(..., description="Training data start date"),
    end_date: str = Query(..., description="Training data end date")
):
    """Train value identification model"""
    try:
        # Get salary and projection data
        salary_data = db.get_dfs_projections()
        projection_data = db.get_daily_dfs_data()
        
        if salary_data.empty or projection_data.empty:
            raise HTTPException(status_code=400, detail="No salary/projection data available")
        
        # Train model
        results = ml_trainer.train_value_model(salary_data, projection_data)
        
        if 'error' in results:
            raise HTTPException(status_code=500, detail=results['error'])
        
        return {
            "message": "Value model training completed",
            "results": results
        }
    except Exception as e:
        logger.error(f"Error training value model: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ml/predict-fantasy-points")
async def predict_fantasy_points(
    features: List[Dict[str, Any]]
):
    """Make fantasy points predictions"""
    try:
        # Convert features to DataFrame
        features_df = pd.DataFrame(features)
        
        # Make predictions
        results = ml_trainer.predict_fantasy_points(features_df)
        
        if 'error' in results:
            raise HTTPException(status_code=500, detail=results['error'])
        
        return {
            "message": "Fantasy points predictions completed",
            "predictions": results['predictions'],
            "model_confidence": results['model_confidence']
        }
    except Exception as e:
        logger.error(f"Error making predictions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== ADVANCED ANALYTICS ENDPOINTS =====

@app.post("/analytics/confidence-intervals")
async def calculate_confidence_intervals(
    predictions: List[float],
    confidence_level: float = Query(0.95, description="Confidence level (0.0-1.0)"),
    method: str = Query("bootstrap", description="Method for calculating intervals")
):
    """Calculate confidence intervals for predictions"""
    try:
        predictions_array = np.array(predictions)
        
        results = advanced_analytics.calculate_confidence_intervals(
            predictions_array, 
            confidence_level, 
            method
        )
        
        if 'error' in results:
            raise HTTPException(status_code=500, detail=results['error'])
        
        return {
            "message": "Confidence intervals calculated successfully",
            "results": results
        }
    except Exception as e:
        logger.error(f"Error calculating confidence intervals: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analytics/percentile-analysis")
async def run_percentile_analysis(
    player_data: List[Dict[str, Any]],
    percentiles: List[float] = Query([10, 25, 50, 75, 90, 95, 99], description="Percentiles to calculate")
):
    """Run percentile-based ceiling/floor analysis"""
    try:
        # Convert to DataFrame
        df = pd.DataFrame(player_data)
        
        results = advanced_analytics.percentile_analysis(df, percentiles)
        
        if 'error' in results:
            raise HTTPException(status_code=500, detail=results['error'])
        
        return {
            "message": "Percentile analysis completed successfully",
            "results": results
        }
    except Exception as e:
        logger.error(f"Error in percentile analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analytics/correlation-analysis")
async def run_correlation_analysis(
    factors: List[Dict[str, Any]],
    method: str = Query("pearson", description="Correlation method")
):
    """Run factor correlation analysis"""
    try:
        # Convert to DataFrame
        df = pd.DataFrame(factors)
        
        results = advanced_analytics.correlation_analysis(df, method)
        
        if 'error' in results:
            raise HTTPException(status_code=500, detail=results['error'])
        
        return {
            "message": "Correlation analysis completed successfully",
            "results": results
        }
    except Exception as e:
        logger.error(f"Error in correlation analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analytics/time-series-analysis")
async def run_time_series_analysis(
    player_data: List[Dict[str, Any]],
    periods: int = Query(30, description="Number of periods to analyze")
):
    """Run time series analysis for trends"""
    try:
        # Convert to DataFrame
        df = pd.DataFrame(player_data)
        
        results = advanced_analytics.time_series_analysis(df, periods)
        
        if 'error' in results:
            raise HTTPException(status_code=500, detail=results['error'])
        
        return {
            "message": "Time series analysis completed successfully",
            "results": results
        }
    except Exception as e:
        logger.error(f"Error in time series analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analytics/monte-carlo-risk-analysis")
async def run_monte_carlo_risk_analysis(
    lineup_data: List[Dict[str, Any]],
    iterations: int = Query(10000, description="Number of Monte Carlo iterations")
):
    """Run Monte Carlo risk analysis for lineups"""
    try:
        results = advanced_analytics.monte_carlo_risk_analysis(lineup_data, iterations)
        
        if 'error' in results:
            raise HTTPException(status_code=500, detail=results['error'])
        
        return {
            "message": "Monte Carlo risk analysis completed successfully",
            "results": results
        }
    except Exception as e:
        logger.error(f"Error in Monte Carlo risk analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== VALUE ANALYSIS ENDPOINTS =====

@app.get("/value/analysis/{game_date}")
async def get_value_analysis(
    game_date: str,
    season: Optional[str] = Query(None, description="NBA season filter")
):
    """Get salary-based value analysis for a given date"""
    try:
        results = value_analyzer.get_value_analysis(game_date, season)
        
        if results.empty:
            return {"message": "No value data available", "data": []}
        
        return {
            "message": "Value analysis completed successfully",
            "game_date": game_date,
            "count": len(results),
            "data": results.to_dict('records')
        }
    except Exception as e:
        logger.error(f"Error in value analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/value/tier-rankings/{game_date}")
async def get_tier_rankings(
    game_date: str,
    tier: Optional[str] = Query(None, description="Salary tier: elite, high, mid, low, minimum")
):
    """Get value rankings by salary tier"""
    try:
        results = value_analyzer.get_tier_value_rankings(game_date, tier)
        
        if results.empty:
            return {"message": "No tier rankings available", "data": []}
        
        return {
            "message": "Tier rankings retrieved successfully",
            "game_date": game_date,
            "tier": tier or "all",
            "count": len(results),
            "data": results.to_dict('records')
        }
    except Exception as e:
        logger.error(f"Error getting tier rankings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/value/best-values/{game_date}")
async def get_best_values(
    game_date: str,
    limit: int = Query(20, description="Number of players to return")
):
    """Get the best value players across all tiers"""
    try:
        results = value_analyzer.get_best_values(game_date, limit)
        
        if results.empty:
            return {"message": "No value players found", "data": []}
        
        return {
            "message": "Best value players retrieved successfully",
            "game_date": game_date,
            "limit": limit,
            "count": len(results),
            "data": results.to_dict('records')
        }
    except Exception as e:
        logger.error(f"Error getting best values: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== INJURY IMPACT ENDPOINTS =====

@app.get("/injury/impact/{player_id}")
async def get_injury_impact(player_id: int):
    """Analyze injury impact and find replacement players"""
    try:
        analysis = injury_analyzer.analyze_injury_impact(player_id)
        
        if 'error' in analysis:
            raise HTTPException(status_code=404, detail=analysis['error'])
        
        return {
            "message": "Injury impact analysis completed successfully",
            "player_id": player_id,
            "data": analysis
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing injury impact: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/injury/all-impacts")
async def get_all_injury_impacts():
    """Get impact analysis for all active injuries"""
    try:
        results = injury_analyzer.get_all_active_injuries_impact()
        
        if results.empty:
            return {"message": "No active injuries found", "data": []}
        
        return {
            "message": "All injury impacts analyzed successfully",
            "count": len(results),
            "data": results.to_dict('records')
        }
    except Exception as e:
        logger.error(f"Error analyzing all injuries: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "ml_service.api:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=True
    )
