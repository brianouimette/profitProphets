"""
Database connection and data access for ML service
Handles connections to MySQL HeatWave and data retrieval
"""

import pandas as pd
from typing import Optional, Dict, Any, List
import mysql.connector
from sqlalchemy import create_engine, text
from ml_service.config import config
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MLDatabase:
    """Database access class for ML service using MySQL HeatWave"""
    
    def __init__(self):
        """Initialize database connection"""
        self.engine = None
        self.connection = None
        self._connect()
    
    def _connect(self):
        """Establish connection to MySQL HeatWave"""
        try:
            if not config.HEATWAVE_HOST or not config.HEATWAVE_USER or not config.HEATWAVE_PASSWORD:
                logger.warning("⚠️ HeatWave credentials not configured - using mock database")
                self.engine = None
                return
            
            # Create SQLAlchemy engine for pandas operations with SSL support
            connection_string = (
                f"mysql+mysqlconnector://{config.HEATWAVE_USER}:"
                f"{config.HEATWAVE_PASSWORD}@{config.HEATWAVE_HOST}:"
                f"{config.HEATWAVE_PORT}/{config.HEATWAVE_DATABASE}"
            )
            # Add SSL configuration for Oracle Cloud MySQL HeatWave
            connect_args = {
                'ssl_disabled': False,
                'ssl_verify_cert': False,
                'ssl_verify_identity': False
            }
            self.engine = create_engine(
                connection_string, 
                echo=False,
                connect_args=connect_args
            )
            
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            logger.info("✅ Connected to MySQL HeatWave database")
        except Exception as e:
            logger.warning(f"⚠️ Failed to connect to HeatWave database: {e}")
            logger.info("📝 Using mock database mode")
            self.engine = None
    
    def _check_connection(self) -> bool:
        """Check if database connection is available"""
        if self.engine is None:
            logger.warning("Database not connected - returning empty DataFrame")
            return False
        return True
    
    def test_connection(self) -> bool:
        """Test database connection"""
        return self.engine is not None
    
    def get_players(self, limit: Optional[int] = None) -> pd.DataFrame:
        """Get all players data"""
        if not self._check_connection():
            return pd.DataFrame()
        
        try:
            query = "SELECT * FROM players"
            if limit:
                query += f" LIMIT {limit}"
            
            df = pd.read_sql(query, self.engine)
            logger.info(f"✅ Retrieved {len(df)} players")
            return df
        except Exception as e:
            logger.error(f"❌ Error getting players: {e}")
            return pd.DataFrame()
    
    def get_teams(self, limit: Optional[int] = None) -> pd.DataFrame:
        """Get all teams data"""
        if not self._check_connection():
            return pd.DataFrame()
        
        try:
            query = "SELECT * FROM teams"
            if limit:
                query += f" LIMIT {limit}"
            
            df = pd.read_sql(query, self.engine)
            logger.info(f"✅ Retrieved {len(df)} teams")
            return df
        except Exception as e:
            logger.error(f"❌ Error getting teams: {e}")
            return pd.DataFrame()
    
    def get_games(self, season: Optional[str] = None, limit: Optional[int] = None) -> pd.DataFrame:
        """Get all games data"""
        if not self._check_connection():
            return pd.DataFrame()
        
        try:
            query = "SELECT * FROM games WHERE 1=1"
            if season:
                query += f" AND season = '{season}'"
            query += " ORDER BY game_date DESC"
            if limit:
                query += f" LIMIT {limit}"
            
            df = pd.read_sql(query, self.engine)
            logger.info(f"✅ Retrieved {len(df)} games")
            return df
        except Exception as e:
            logger.error(f"❌ Error getting games: {e}")
            return pd.DataFrame()
    
    def get_player_game_logs(self, limit: Optional[int] = None) -> pd.DataFrame:
        """Get all player game logs data"""
        if not self._check_connection():
            return pd.DataFrame()
        
        try:
            query = "SELECT * FROM player_game_logs"
            if limit:
                query += f" LIMIT {limit}"
            
            df = pd.read_sql(query, self.engine)
            logger.info(f"✅ Retrieved {len(df)} player game logs")
            return df
        except Exception as e:
            logger.error(f"❌ Error getting player game logs: {e}")
            return pd.DataFrame()
    
    def get_dfs_projections(self, limit: Optional[int] = None) -> pd.DataFrame:
        """Get all DFS projections data"""
        if not self._check_connection():
            return pd.DataFrame()
        
        try:
            query = "SELECT * FROM dfs_projections"
            if limit:
                query += f" LIMIT {limit}"
            
            df = pd.read_sql(query, self.engine)
            logger.info(f"✅ Retrieved {len(df)} DFS projections")
            return df
        except Exception as e:
            logger.error(f"❌ Error getting DFS projections: {e}")
            return pd.DataFrame()
    
    def get_daily_dfs_data(self, limit: Optional[int] = None) -> pd.DataFrame:
        """Get all daily DFS data"""
        if not self._check_connection():
            return pd.DataFrame()
        
        try:
            query = "SELECT * FROM daily_dfs_data"
            if limit:
                query += f" LIMIT {limit}"
            
            df = pd.read_sql(query, self.engine)
            logger.info(f"✅ Retrieved {len(df)} daily DFS data")
            return df
        except Exception as e:
            logger.error(f"❌ Error getting daily DFS data: {e}")
            return pd.DataFrame()
    
    def get_game_lineups(self, limit: Optional[int] = None) -> pd.DataFrame:
        """Get all game lineups data"""
        if not self._check_connection():
            return pd.DataFrame()
        
        try:
            query = "SELECT * FROM game_lineups"
            if limit:
                query += f" LIMIT {limit}"
            
            df = pd.read_sql(query, self.engine)
            logger.info(f"✅ Retrieved {len(df)} game lineups")
            return df
        except Exception as e:
            logger.error(f"❌ Error getting game lineups: {e}")
            return pd.DataFrame()
    
    def get_player_injuries(self, limit: Optional[int] = None) -> pd.DataFrame:
        """Get all player injuries data"""
        if not self._check_connection():
            return pd.DataFrame()
        
        try:
            query = "SELECT * FROM injuries"
            if limit:
                query += f" LIMIT {limit}"
            
            df = pd.read_sql(query, self.engine)
            logger.info(f"✅ Retrieved {len(df)} player injuries")
            return df
        except Exception as e:
            logger.error(f"❌ Error getting player injuries: {e}")
            return pd.DataFrame()
    
    def get_historical_data_summary(self) -> Dict[str, Any]:
        """Get summary of all historical data"""
        if not self._check_connection():
            return {"error": "Database not connected"}
        
        try:
            summary = {}
            
            # Get counts for each table
            tables = ['players', 'teams', 'games', 'player_game_logs', 'injuries', 'dfs_projections', 'daily_dfs_data']
            
            for table in tables:
                query = f"SELECT COUNT(*) as count FROM {table}"
                result = pd.read_sql(query, self.engine)
                summary[table] = result['count'].iloc[0]
            
            logger.info("✅ Retrieved historical data summary")
            return summary
        except Exception as e:
            logger.error(f"❌ Error getting historical data summary: {e}")
            return {"error": str(e)}

# Global database instance
db = MLDatabase()