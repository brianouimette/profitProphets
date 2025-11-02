"""
ML Service Configuration
Handles environment variables and configuration for the ML service
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables - try env.test first, then .env
from pathlib import Path
project_root = Path(__file__).parent.parent
env_test = project_root / 'env.test'
env_file = project_root / '.env'

if env_test.exists():
    load_dotenv(env_test, override=True)
elif env_file.exists():
    load_dotenv(env_file)
else:
    load_dotenv()

class MLConfig:
    """Configuration class for ML service"""
    
    # MySQL HeatWave Configuration
    HEATWAVE_HOST: str = os.getenv('HEATWAVE_HOST', '')
    HEATWAVE_PORT: int = int(os.getenv('HEATWAVE_PORT', '3306'))
    HEATWAVE_USER: str = os.getenv('HEATWAVE_USER', '')
    HEATWAVE_PASSWORD: str = os.getenv('HEATWAVE_PASSWORD', '')
    HEATWAVE_DATABASE: str = os.getenv('HEATWAVE_DATABASE', 'nba_fantasy')
    
    # Alternative names for compatibility
    MYSQL_HOST: str = os.getenv('MYSQL_HOST', HEATWAVE_HOST)
    MYSQL_PORT: int = int(os.getenv('MYSQL_PORT', str(HEATWAVE_PORT)))
    MYSQL_USER: str = os.getenv('MYSQL_USER', HEATWAVE_USER)
    MYSQL_PASSWORD: str = os.getenv('MYSQL_PASSWORD', HEATWAVE_PASSWORD)
    MYSQL_DATABASE: str = os.getenv('MYSQL_DATABASE', HEATWAVE_DATABASE)
    
    # Model Configuration
    MODEL_CACHE_DIR: str = os.getenv('MODEL_CACHE_DIR', './ml_models')
    HISTORICAL_DATA_PATH: str = os.getenv('HISTORICAL_DATA_PATH', './historical_data')
    
    # Performance Configuration
    MAX_WORKERS: int = int(os.getenv('MAX_WORKERS', '4'))
    BATCH_SIZE: int = int(os.getenv('BATCH_SIZE', '1000'))
    
    # Model Parameters
    CROSS_VALIDATION_FOLDS: int = 5
    RANDOM_STATE: int = 42
    
    # Data Quality Thresholds
    MIN_GAMES_FOR_ANALYSIS: int = 10
    MIN_SEASONS_FOR_TRENDS: int = 2
    
    # API Configuration
    API_HOST: str = os.getenv('ML_API_HOST', '0.0.0.0')
    API_PORT: int = int(os.getenv('ML_API_PORT', '8001'))
    
    @classmethod
    def validate(cls) -> bool:
        """Validate that all required configuration is present"""
        required_vars = [
            'HEATWAVE_HOST',
            'HEATWAVE_USER',
            'HEATWAVE_PASSWORD'
        ]
        
        missing_vars = [var for var in required_vars if not getattr(cls, var)]
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {missing_vars}")
        
        return True

# Global config instance
config = MLConfig()
