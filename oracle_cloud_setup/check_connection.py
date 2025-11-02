#!/usr/bin/env python3
"""
Oracle Cloud Connection Checker
Verify connection to your existing Oracle Cloud infrastructure
"""

import os
import sys
import mysql.connector
from sqlalchemy import create_engine, text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_heatwave_connection():
    """Check connection to MySQL HeatWave"""
    try:
        # Get connection details from environment
        host = os.getenv('HEATWAVE_HOST', os.getenv('MYSQL_HOST'))
        port = int(os.getenv('HEATWAVE_PORT', os.getenv('MYSQL_PORT', '3306')))
        user = os.getenv('HEATWAVE_USER', os.getenv('MYSQL_USER'))
        password = os.getenv('HEATWAVE_PASSWORD', os.getenv('MYSQL_PASSWORD'))
        database = os.getenv('HEATWAVE_DATABASE', os.getenv('MYSQL_DATABASE', 'nba_fantasy'))
        
        logger.info(f"🔍 Testing connection to: {host}:{port}")
        logger.info(f"📊 Database: {database}")
        logger.info(f"👤 User: {user}")
        
        # Test connection
        connection_string = f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/{database}"
        engine = create_engine(connection_string, echo=False)
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 as test"))
            test_value = result.fetchone()[0]
            
        if test_value == 1:
            logger.info("✅ HeatWave connection successful!")
            return True
        else:
            logger.error("❌ HeatWave connection failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ HeatWave connection error: {e}")
        return False

def check_environment():
    """Check if environment variables are set"""
    required_vars = [
        'HEATWAVE_HOST', 'HEATWAVE_USER', 'HEATWAVE_PASSWORD'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var) and not os.getenv(var.replace('HEATWAVE_', 'MYSQL_')):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"❌ Missing environment variables: {missing_vars}")
        logger.info("📝 Please set these in your .env file:")
        for var in missing_vars:
            logger.info(f"   {var}=your_value")
        return False
    
    logger.info("✅ Environment variables configured")
    return True

def main():
    """Main connection check"""
    logger.info("🔍 Checking Oracle Cloud connection...")
    
    # Check environment
    if not check_environment():
        logger.error("❌ Environment check failed")
        return 1
    
    # Check HeatWave connection
    if not check_heatwave_connection():
        logger.error("❌ HeatWave connection failed")
        return 1
    
    logger.info("🎉 All connections successful!")
    logger.info("✅ Ready to run setup_oracle_cloud.py")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
