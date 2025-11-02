#!/usr/bin/env python3
"""
Execute MySQL Schema Script
Creates all necessary tables in the Oracle Cloud MySQL HeatWave database
"""

import os
import sys
import mysql.connector
from mysql.connector import Error
import logging
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
project_root = Path(__file__).parent.parent
env_test = project_root / 'env.test'
env_file = project_root / '.env'

if env_test.exists():
    load_dotenv(env_test)
elif env_file.exists():
    load_dotenv(env_file)
else:
    load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def execute_schema():
    """Execute the MySQL schema script"""
    try:
        # Get connection details
        host = os.getenv('HEATWAVE_HOST')
        port = int(os.getenv('HEATWAVE_PORT', '3306'))
        user = os.getenv('HEATWAVE_USER')
        password = os.getenv('HEATWAVE_PASSWORD')
        database = os.getenv('HEATWAVE_DATABASE', 'nba_fantasy')
        
        logger.info("🔍 Connecting to MySQL HeatWave...")
        logger.info(f"📍 Host: {host}:{port}")
        logger.info(f"🗄️ Database: {database}")
        
        # Connect to database
        connection = mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            autocommit=False  # Use transactions
        )
        
        if not connection.is_connected():
            logger.error("❌ Failed to connect to database")
            return False
        
        logger.info("✅ Connected to database")
        
        # Read schema file
        schema_file = Path(__file__).parent / 'mysql_schema.sql'
        if not schema_file.exists():
            logger.error(f"❌ Schema file not found: {schema_file}")
            return False
        
        logger.info(f"📄 Reading schema file: {schema_file}")
        
        cursor = connection.cursor()
        
        # Read and parse SQL file line by line
        current_statement = []
        statements = []
        
        with open(schema_file, 'r') as f:
            for line in f:
                line_stripped = line.strip()
                
                # Skip empty lines and full-line comments
                if not line_stripped or line_stripped.startswith('--'):
                    continue
                
                # Skip CREATE DATABASE and USE statements
                line_upper = line_stripped.upper()
                if 'CREATE DATABASE' in line_upper or line_upper.startswith('USE '):
                    logger.info(f"⏭️ Skipping: {line_stripped}")
                    continue
                
                # Skip GRANT and FLUSH (they're commented in schema anyway)
                if line_upper.startswith('GRANT') or line_upper.startswith('FLUSH'):
                    continue
                
                # Remove inline comments
                if '--' in line:
                    comment_idx = line.find('--')
                    line = line[:comment_idx]
                
                current_statement.append(line)
                
                # If line ends with semicolon, we have a complete statement
                if line.rstrip().endswith(';'):
                    statement = ''.join(current_statement).strip()
                    if statement and len(statement) > 10:  # Filter out tiny fragments
                        statements.append(statement)
                    current_statement = []
        
        # Handle any remaining statement
        if current_statement:
            statement = ''.join(current_statement).strip()
            if statement and len(statement) > 10:
                statements.append(statement)
        
        logger.info(f"📋 Found {len(statements)} SQL statements to execute...")
        
        success_count = 0
        error_count = 0
        skipped_count = 0
        
        for i, statement in enumerate(statements, 1):
            try:
                # Get statement type for logging
                stmt_type = statement[:30].replace('\n', ' ').strip()
                if len(statement) > 30:
                    stmt_type += "..."
                
                logger.info(f"   [{i}/{len(statements)}] Executing: {stmt_type}")
                
                cursor.execute(statement)
                success_count += 1
                
            except Error as e:
                # Some errors are expected (like table already exists)
                error_msg = str(e).lower()
                if 'already exists' in error_msg:
                    logger.warning(f"   ⚠️ [{i}] Already exists (skipping)")
                    skipped_count += 1
                else:
                    logger.error(f"   ❌ [{i}] Error: {str(e)[:200]}")
                    error_count += 1
        
        # Commit all changes
        connection.commit()
        
        logger.info(f"✅ Schema execution complete!")
        logger.info(f"   ✅ Success: {success_count} statements")
        if skipped_count > 0:
            logger.info(f"   ⏭️ Skipped (already exists): {skipped_count} statements")
        if error_count > 0:
            logger.warning(f"   ❌ Errors: {error_count} statements")
        
        # Verify tables were created
        logger.info("🔍 Verifying tables...")
        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor.fetchall()]
        logger.info(f"📊 Found {len(tables)} tables: {', '.join(tables)}")
        
        # Check views
        cursor.execute("SHOW FULL TABLES WHERE Table_Type = 'VIEW'")
        views = [view[0] for view in cursor.fetchall()]
        if views:
            logger.info(f"📊 Found {len(views)} views: {', '.join(views)}")
        
        cursor.close()
        connection.close()
        
        logger.info("🎉 Schema setup completed successfully!")
        return True
        
    except Error as e:
        logger.error(f"❌ MySQL Error: {e}")
        if connection and connection.is_connected():
            connection.rollback()
            connection.close()
        return False
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return False

def main():
    """Main function"""
    logger.info("🚀 Starting MySQL schema execution...")
    
    success = execute_schema()
    
    if success:
        logger.info("✅ Schema execution completed successfully!")
        return 0
    else:
        logger.error("❌ Schema execution failed. Check logs for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
