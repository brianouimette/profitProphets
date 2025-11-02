"""
HeatWave ML Analyzer
Enhanced ML models with MySQL HeatWave integration for NBA fantasy analysis
"""

import pandas as pd
from sqlalchemy import create_engine, text
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import joblib
import os

logger = logging.getLogger(__name__)

class HeatWaveMLAnalyzer:
    """Enhanced ML analyzer using MySQL HeatWave for data processing"""
    
    def __init__(self, heatwave_config: Dict[str, str]):
        """
        Initialize the HeatWave ML analyzer
        
        Args:
            heatwave_config: MySQL HeatWave connection configuration
        """
        self.heatwave_config = heatwave_config
        self.engine = None
        self.models = {}
        self.model_cache_dir = './ml_models'
        
        # Create model cache directory
        os.makedirs(self.model_cache_dir, exist_ok=True)
        
    def connect(self) -> bool:
        """Connect to MySQL HeatWave database"""
        try:
            connection_string = (
                f"mysql+mysqlconnector://{self.heatwave_config['user']}:"
                f"{self.heatwave_config['password']}@{self.heatwave_config['host']}:"
                f"{self.heatwave_config['port']}/{self.heatwave_config['database']}"
            )
            self.engine = create_engine(connection_string, echo=False)
            
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            logger.info("✅ Connected to MySQL HeatWave")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to HeatWave: {e}")
            return False
    
    def get_team_defense_analysis(self, season_year: Optional[int] = None) -> pd.DataFrame:
        """
        Analyze team defense using HeatWave for fast data processing
        
        Args:
            season_year: Season year to analyze (None for all seasons)
        
        Returns:
            DataFrame with team defense analysis
        """
        try:
            query = """
            SELECT 
                t.id as team_id,
                t.abbreviation as team,
                p.position,
                AVG(pgl.fantasy_points) as avg_fantasy_points_allowed,
                STDDEV(pgl.fantasy_points) as defense_consistency,
                COUNT(pgl.id) as games_analyzed,
                -- HeatWave can calculate advanced metrics
                AVG(pgl.rebounds + pgl.assists) as avg_combined_stats_allowed,
                AVG(pgl.steals + pgl.blocks) as avg_defensive_stats_allowed
            FROM teams t
            JOIN games g ON (t.id = g.home_team_id OR t.id = g.away_team_id)
            JOIN player_game_logs pgl ON g.id = pgl.game_id
            JOIN players p ON pgl.player_id = p.id
            WHERE g.status = 'FINAL'
            AND g.game_date >= %s
            GROUP BY t.id, t.abbreviation, p.position
            ORDER BY avg_fantasy_points_allowed DESC
            """
            
            start_date = f"{season_year}-01-01" if season_year else "2020-01-01"
            
            df = pd.read_sql(query, self.engine, params=[start_date])
            
            # Add custom ML analysis
            df['defense_rating'] = self._calculate_defense_rating(df)
            df['consistency_score'] = self._calculate_consistency_score(df)
            df['overall_defense_score'] = (
                df['defense_rating'] * 0.6 + 
                df['consistency_score'] * 0.4
            )
            
            logger.info(f"✅ Team defense analysis completed: {len(df)} records")
            return df
            
        except Exception as e:
            logger.error(f"❌ Error in team defense analysis: {e}")
            return pd.DataFrame()
    
    def get_player_performance_prediction(self, player_id: int, game_date: str) -> Dict[str, Any]:
        """
        Predict player performance using HeatWave + ML
        
        Args:
            player_id: Player ID to analyze
            game_date: Game date for prediction
        
        Returns:
            Dictionary with prediction results
        """
        try:
            # Get player features using HeatWave
            features_query = """
            SELECT 
                p.id as player_id,
                p.position,
                AVG(pgl.fantasy_points) as recent_avg,
                STDDEV(pgl.fantasy_points) as consistency,
                COUNT(pgl.id) as recent_games,
                AVG(pgl.minutes_played) as avg_minutes,
                AVG(pgl.rebounds + pgl.assists) as avg_combined_stats,
                -- Recent trend analysis
                AVG(CASE WHEN pgl.created_at >= DATE_SUB(NOW(), INTERVAL 10 DAY) 
                    THEN pgl.fantasy_points END) as recent_10_day_avg,
                AVG(CASE WHEN pgl.created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY) 
                    THEN pgl.fantasy_points END) as recent_30_day_avg
            FROM players p
            LEFT JOIN player_game_logs pgl ON p.id = pgl.player_id
            LEFT JOIN games g ON pgl.game_id = g.id
            WHERE p.id = %s
            AND g.game_date >= DATE_SUB(%s, INTERVAL 30 DAY)
            GROUP BY p.id, p.position
            """
            
            features_df = pd.read_sql(features_query, self.engine, params=[player_id, game_date])
            
            if features_df.empty:
                return {'error': 'Player not found or no recent data'}
            
            features = features_df.iloc[0]
            
            # Use ML model for prediction
            prediction = self._predict_player_performance(features)
            
            return {
                'player_id': player_id,
                'game_date': game_date,
                'predicted_fantasy_points': prediction['fantasy_points'],
                'confidence': prediction['confidence'],
                'factors': {
                    'recent_avg': float(features['recent_avg']),
                    'consistency': float(features['consistency']),
                    'recent_games': int(features['recent_games']),
                    'position': features['position']
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error in player performance prediction: {e}")
            return {'error': str(e)}
    
    def get_injury_impact_analysis(self, injured_player_id: int) -> Dict[str, Any]:
        """
        Analyze injury impact and find replacement players
        
        Args:
            injured_player_id: ID of injured player
        
        Returns:
            Dictionary with injury impact analysis
        """
        try:
            # Get injury details
            injury_query = """
            SELECT 
                i.*,
                p.first_name,
                p.last_name,
                p.position,
                t.abbreviation as team
            FROM injuries i
            JOIN players p ON i.player_id = p.id
            JOIN teams t ON p.team_id = t.id
            WHERE i.player_id = %s
            AND i.status = 'ACTIVE'
            ORDER BY i.start_date DESC
            LIMIT 1
            """
            
            injury_df = pd.read_sql(injury_query, self.engine, params=[injured_player_id])
            
            if injury_df.empty:
                return {'error': 'No active injury found for player'}
            
            injury = injury_df.iloc[0]
            
            # Find replacement players using HeatWave
            replacement_query = """
            SELECT 
                p.id,
                p.first_name,
                p.last_name,
                p.position,
                t.abbreviation as team,
                AVG(pgl.fantasy_points) as avg_performance,
                STDDEV(pgl.fantasy_points) as consistency,
                COUNT(pgl.id) as games_played,
                -- Recent performance
                AVG(CASE WHEN pgl.created_at >= DATE_SUB(NOW(), INTERVAL 10 DAY) 
                    THEN pgl.fantasy_points END) as recent_10_day_avg
            FROM players p
            JOIN teams t ON p.team_id = t.id
            LEFT JOIN player_game_logs pgl ON p.id = pgl.player_id
            WHERE p.position = %s
            AND p.id != %s
            AND p.id NOT IN (
                SELECT player_id FROM injuries 
                WHERE status = 'ACTIVE' AND player_id = p.id
            )
            GROUP BY p.id, p.first_name, p.last_name, p.position, t.abbreviation
            HAVING games_played >= 5
            ORDER BY recent_10_day_avg DESC, avg_performance DESC
            LIMIT 10
            """
            
            replacements_df = pd.read_sql(
                replacement_query, 
                self.engine, 
                params=[injury['position'], injured_player_id]
            )
            
            return {
                'injured_player': {
                    'id': injury['player_id'],
                    'name': f"{injury['first_name']} {injury['last_name']}",
                    'position': injury['position'],
                    'team': injury['team'],
                    'injury_type': injury['injury_type'],
                    'status': injury['status'],
                    'expected_return': injury['expected_return']
                },
                'replacement_options': replacements_df.to_dict('records'),
                'impact_analysis': self._analyze_injury_impact(injury, replacements_df)
            }
            
        except Exception as e:
            logger.error(f"❌ Error in injury impact analysis: {e}")
            return {'error': str(e)}
    
    def get_salary_value_analysis(self, game_date: str) -> pd.DataFrame:
        """
        Analyze salary-based value for daily fantasy
        
        Args:
            game_date: Date to analyze
        
        Returns:
            DataFrame with value analysis
        """
        try:
            query = """
            SELECT 
                p.id as player_id,
                p.first_name,
                p.last_name,
                p.position,
                t.abbreviation as team,
                dp.salary,
                dp.projected_fantasy_points,
                dp.ownership_percentage,
                dp.ceiling,
                dp.floor,
                -- Value calculations
                (dp.projected_fantasy_points / dp.salary * 1000) as value_score,
                (dp.ceiling / dp.salary * 1000) as ceiling_value,
                (dp.floor / dp.salary * 1000) as floor_value,
                -- Recent performance for context
                AVG(pgl.fantasy_points) as recent_avg,
                STDDEV(pgl.fantasy_points) as recent_consistency
            FROM players p
            JOIN teams t ON p.team_id = t.id
            JOIN dfs_projections dp ON p.id = dp.player_id
            JOIN games g ON dp.game_id = g.id
            LEFT JOIN player_game_logs pgl ON p.id = pgl.player_id
            WHERE g.game_date = %s
            AND pgl.created_at >= DATE_SUB(%s, INTERVAL 30 DAY)
            GROUP BY p.id, p.first_name, p.last_name, p.position, t.abbreviation,
                     dp.salary, dp.projected_fantasy_points, dp.ownership_percentage,
                     dp.ceiling, dp.floor
            ORDER BY value_score DESC
            """
            
            df = pd.read_sql(query, self.engine, params=[game_date, game_date])
            
            # Add ML-based value scoring
            df['ml_value_score'] = self._calculate_ml_value_score(df)
            df['risk_score'] = self._calculate_risk_score(df)
            df['recommendation'] = self._generate_recommendations(df)
            
            logger.info(f"✅ Salary value analysis completed: {len(df)} players")
            return df
            
        except Exception as e:
            logger.error(f"❌ Error in salary value analysis: {e}")
            return pd.DataFrame()
    
    def _calculate_defense_rating(self, df: pd.DataFrame) -> pd.Series:
        """Calculate custom defense rating"""
        return (df['avg_fantasy_points_allowed'] * 0.7 + 
                df['defense_consistency'] * 0.3)
    
    def _calculate_consistency_score(self, df: pd.DataFrame) -> pd.Series:
        """Calculate consistency score"""
        return 1 - (df['defense_consistency'] / df['avg_fantasy_points_allowed'])
    
    def _predict_player_performance(self, features: pd.Series) -> Dict[str, float]:
        """Predict player performance using ML model"""
        # This would use a trained ML model
        # For now, return a simple prediction
        base_prediction = features['recent_avg'] or 0
        confidence = min(0.9, max(0.1, 1 - (features['consistency'] or 0) / 20))
        
        return {
            'fantasy_points': float(base_prediction),
            'confidence': float(confidence)
        }
    
    def _analyze_injury_impact(self, injury: pd.Series, replacements: pd.DataFrame) -> Dict[str, Any]:
        """Analyze the impact of an injury"""
        if replacements.empty:
            return {'impact_level': 'HIGH', 'reason': 'No suitable replacements found'}
        
        best_replacement = replacements.iloc[0]
        performance_gap = (injury.get('recent_avg', 0) or 0) - best_replacement['avg_performance']
        
        if performance_gap > 5:
            impact_level = 'HIGH'
        elif performance_gap > 2:
            impact_level = 'MEDIUM'
        else:
            impact_level = 'LOW'
        
        return {
            'impact_level': impact_level,
            'performance_gap': float(performance_gap),
            'best_replacement': best_replacement.to_dict()
        }
    
    def _calculate_ml_value_score(self, df: pd.DataFrame) -> pd.Series:
        """Calculate ML-based value score"""
        # Simple ML-based value calculation
        return (df['value_score'] * 0.6 + 
                df['recent_avg'] / df['salary'] * 1000 * 0.4)
    
    def _calculate_risk_score(self, df: pd.DataFrame) -> pd.Series:
        """Calculate risk score for players"""
        return (df['recent_consistency'] / df['recent_avg']).fillna(0)
    
    def _generate_recommendations(self, df: pd.DataFrame) -> pd.Series:
        """Generate recommendations for players"""
        def get_recommendation(row):
            if row['ml_value_score'] > 5 and row['risk_score'] < 0.3:
                return 'STRONG_BUY'
            elif row['ml_value_score'] > 3 and row['risk_score'] < 0.5:
                return 'BUY'
            elif row['ml_value_score'] < 2 or row['risk_score'] > 0.7:
                return 'AVOID'
            else:
                return 'HOLD'
        
        return df.apply(get_recommendation, axis=1)

def main():
    """Test the HeatWave ML analyzer"""
    
    # HeatWave configuration
    heatwave_config = {
        'host': os.getenv('HEATWAVE_HOST', 'localhost'),
        'port': int(os.getenv('HEATWAVE_PORT', '3306')),
        'user': os.getenv('HEATWAVE_USER', 'root'),
        'password': os.getenv('HEATWAVE_PASSWORD', ''),
        'database': os.getenv('HEATWAVE_DATABASE', 'nba_fantasy')
    }
    
    # Create analyzer
    analyzer = HeatWaveMLAnalyzer(heatwave_config)
    
    if analyzer.connect():
        logger.info("✅ HeatWave ML Analyzer ready!")
        
        # Test team defense analysis
        defense_analysis = analyzer.get_team_defense_analysis(2024)
        logger.info(f"Team defense analysis: {len(defense_analysis)} records")
        
        # Test player prediction
        prediction = analyzer.get_player_performance_prediction(1, '2025-01-22')
        logger.info(f"Player prediction: {prediction}")
        
    else:
        logger.error("❌ Failed to connect to HeatWave")

if __name__ == "__main__":
    main()
