#!/usr/bin/env python3
"""
Oracle Cloud Connection Test Script
Test connection to MySQL HeatWave before full setup
"""

import os
import sys
import mysql.connector
from mysql.connector import Error
import logging
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables - try env.test first, then .env
project_root = Path(__file__).parent.parent
env_test = project_root / 'env.test'
env_file = project_root / '.env'

if env_test.exists():
    load_dotenv(env_test)
elif env_file.exists():
    load_dotenv(env_file)
else:
    load_dotenv()  # Try default .env

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_basic_connection():
    """Test basic MySQL connection"""
    try:
        # Get connection details
        host = os.getenv('HEATWAVE_HOST')
        port = int(os.getenv('HEATWAVE_PORT', '3306'))
        user = os.getenv('HEATWAVE_USER')
        password = os.getenv('HEATWAVE_PASSWORD')
        database = os.getenv('HEATWAVE_DATABASE', 'nba_fantasy')
        
        logger.info("🔍 Testing Oracle Cloud MySQL HeatWave connection...")
        logger.info(f"📍 Host: {host}")
        logger.info(f"🔌 Port: {port}")
        logger.info(f"👤 User: {user}")
        logger.info(f"🗄️ Database: {database}")
        
        # First, connect without specifying database to check/create it
        connection = mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            autocommit=True
        )
        
        if connection.is_connected():
            logger.info("✅ Connection successful!")
            
            # Test basic query
            cursor = connection.cursor()
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            logger.info(f"📊 MySQL Version: {version[0]}")
            
            # Check existing databases
            cursor.execute("SHOW DATABASES")
            databases = [db[0] for db in cursor.fetchall()]
            logger.info(f"📋 Available databases: {databases}")
            
            # Create database if it doesn't exist
            if database not in databases:
                logger.warning(f"⚠️ Database '{database}' not found. Creating it...")
                try:
                    cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{database}`")
                    logger.info(f"✅ Database '{database}' created successfully")
                except Error as db_error:
                    logger.error(f"❌ Failed to create database: {db_error}")
                    logger.error("🔧 You may need to create the database manually or check user permissions")
                    cursor.close()
                    connection.close()
                    return False
            else:
                logger.info(f"✅ Database '{database}' already exists")
            
            # Now connect to the specific database
            cursor.close()
            connection.close()
            
            connection = mysql.connector.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database,
                autocommit=True
            )
            
            if connection.is_connected():
                logger.info(f"✅ Successfully connected to database '{database}'")
                
                # Test a simple query on the database
                cursor = connection.cursor()
                cursor.execute("SELECT DATABASE()")
                current_db = cursor.fetchone()
                logger.info(f"📊 Current database: {current_db[0]}")
                
                cursor.close()
                connection.close()
                
                return True
            
    except Error as e:
        logger.error(f"❌ MySQL Error: {e}")
        if "Unknown database" in str(e):
            logger.info("💡 Tip: The database doesn't exist. The script will try to create it.")
        return False
    except Exception as e:
        logger.error(f"❌ Connection Error: {e}")
        return False

def test_network_connectivity():
    """Test network connectivity to Oracle Cloud"""
    import socket
    
    host = os.getenv('HEATWAVE_HOST')
    port = int(os.getenv('HEATWAVE_PORT', '3306'))
    
    logger.info(f"🌐 Testing network connectivity to {host}:{port}...")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)  # 10 second timeout
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            logger.info("✅ Network connectivity successful!")
            return True
        else:
            logger.error(f"❌ Network connectivity failed (error code: {result})")
            logger.error("🔧 Check your Oracle Cloud security groups and firewall settings")
            return False
            
    except Exception as e:
        logger.error(f"❌ Network test error: {e}")
        return False

def check_environment():
    """Check if all required environment variables are set"""
    required_vars = ['HEATWAVE_HOST', 'HEATWAVE_USER', 'HEATWAVE_PASSWORD']
    
    logger.info("🔍 Checking environment variables...")
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value or value.startswith('your_'):
            missing_vars.append(var)
            logger.warning(f"⚠️ {var}: Not set or using placeholder value")
        else:
            logger.info(f"✅ {var}: Set")
    
    if missing_vars:
        logger.error(f"❌ Missing or invalid environment variables: {missing_vars}")
        logger.info("📝 Please update your .env file with actual Oracle Cloud credentials")
        return False
    
    return True

def main():
    """Main test function"""
    logger.info("🚀 Starting Oracle Cloud connection verification...")
    
    # Check environment
    if not check_environment():
        logger.error("❌ Environment check failed")
        return 1
    
    # Test network connectivity
    if not test_network_connectivity():
        logger.error("❌ Network connectivity test failed")
        logger.info("🔧 Troubleshooting steps:")
        logger.info("   1. Check Oracle Cloud security groups allow port 3306")
        logger.info("   2. Verify your IP address is whitelisted")
        logger.info("   3. Ensure MySQL HeatWave instance is running")
        return 1
    
    # Test MySQL connection
    if not test_basic_connection():
        logger.error("❌ MySQL connection test failed")
        logger.info("🔧 Troubleshooting steps:")
        logger.info("   1. Verify username and password are correct")
        logger.info("   2. Check database name exists or can be created")
        logger.info("   3. Ensure user has proper privileges")
        return 1
    
    logger.info("🎉 All connection tests passed!")
    logger.info("✅ Ready to proceed with full Oracle Cloud setup")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
