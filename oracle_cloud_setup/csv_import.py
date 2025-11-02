#!/usr/bin/env python3
"""
CSV Import Script for NBA Fantasy Data
Imports historical NBA data from CSV files to MySQL HeatWave
"""

import pandas as pd
import mysql.connector
from sqlalchemy import create_engine
import logging
import os
from typing import Dict, List, Optional
from datetime import datetime
import sys
from pathlib import Path
from dotenv import load_dotenv

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

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NBAFantasyDataImporter:
    """Import NBA fantasy data from CSV files to MySQL HeatWave"""
    
    def __init__(self, mysql_config: Dict[str, str]):
        """
        Initialize the importer with MySQL connection config
        
        Args:
            mysql_config: Dictionary with MySQL connection parameters
        """
        self.mysql_config = mysql_config
        self.engine = None
        self.connection = None
        
    def connect(self) -> bool:
        """Connect to MySQL HeatWave database"""
        try:
            # Create SQLAlchemy engine for pandas operations
            connection_string = (
                f"mysql+mysqlconnector://{self.mysql_config['user']}:"
                f"{self.mysql_config['password']}@{self.mysql_config['host']}:"
                f"{self.mysql_config['port']}/{self.mysql_config['database']}"
            )
            self.engine = create_engine(connection_string, echo=False)
            
            # Test connection
            with self.engine.connect() as conn:
                from sqlalchemy import text
                conn.execute(text("SELECT 1"))
            
            logger.info("✅ Connected to MySQL HeatWave database")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to MySQL: {e}")
            return False
    
    def import_csv_file(self, csv_file: str, table_name: str, 
                       chunk_size: int = 1000, 
                       if_exists: str = 'append') -> bool:
        """
        Import a CSV file to MySQL table
        
        Args:
            csv_file: Path to CSV file
            table_name: Target MySQL table name
            chunk_size: Number of rows to process at once
            if_exists: What to do if table exists ('append', 'replace', 'fail')
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not os.path.exists(csv_file):
                logger.error(f"❌ CSV file not found: {csv_file}")
                return False
            
            logger.info(f"📊 Importing {csv_file} to {table_name}...")
            
            # Read CSV in chunks for large files
            total_rows = 0
            chunk_iter = pd.read_csv(csv_file, chunksize=chunk_size)
            
            for i, chunk in enumerate(chunk_iter):
                logger.info(f"   Processing chunk {i+1} ({len(chunk)} rows)...")
                
                # Clean data
                chunk = self.clean_data(chunk, table_name)
                
                if chunk.empty:
                    logger.warning(f"   ⚠️ Chunk {i+1} is empty after cleaning, skipping")
                    continue
                
                # For players table updates (from common_player_info.csv), use UPDATE instead of INSERT
                if table_name == 'players' and os.path.basename(csv_file) == 'common_player_info.csv':
                    logger.info(f"   🔄 Updating existing player records with enriched data...")
                    # Update players with new data
                    from sqlalchemy import text
                    updated_count = 0
                    with self.engine.connect() as conn:
                        for _, row in chunk.iterrows():
                            if pd.notna(row.get('id')):
                                update_fields = []
                                values = {}
                                for col in ['height', 'weight', 'birth_date', 'country']:
                                    if col in row and pd.notna(row[col]):
                                        update_fields.append(f"{col} = :{col}")
                                        values[col] = row[col]
                                
                                if update_fields:
                                    query = text(f"""
                                        UPDATE players 
                                        SET {', '.join(update_fields)}
                                        WHERE id = :id
                                    """)
                                    values['id'] = int(row['id'])
                                    result = conn.execute(query, values)
                                    if result.rowcount > 0:
                                        updated_count += 1
                        conn.commit()
                    logger.info(f"   ✅ Updated {updated_count} player records from chunk {i+1}")
                    total_rows += updated_count
                else:
                    # Regular import
                    chunk.to_sql(
                        table_name, 
                        self.engine, 
                        if_exists=if_exists if i == 0 else 'append',
                        index=False,
                        chunksize=500  # Insert in smaller batches to avoid parameter limits
                    )
                    total_rows += len(chunk)
                    logger.info(f"   ✅ Chunk {i+1} imported successfully")
            
            if table_name == 'players' and os.path.basename(csv_file) == 'common_player_info.csv':
                logger.info(f"✅ Updated {total_rows} player records with enriched data")
            else:
                logger.info(f"✅ Imported {total_rows} rows to {table_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error importing {csv_file}: {e}")
            return False
    
    def map_csv_to_schema(self, df: pd.DataFrame, table_name: str, engine=None) -> pd.DataFrame:
        """
        Map CSV columns to database schema columns
        
        Args:
            df: DataFrame with CSV data
            table_name: Target table name
        
        Returns:
            pd.DataFrame: Mapped DataFrame
        """
        mapped_df = pd.DataFrame()
        
        if table_name == 'teams':
            # Map team.csv columns to teams table
            if 'id' in df.columns:
                mapped_df['id'] = df['id'].astype(int)
            if 'abbreviation' in df.columns:
                mapped_df['abbreviation'] = df['abbreviation']
            if 'city' in df.columns:
                mapped_df['city'] = df['city']
            elif 'nickname' in df.columns:
                # If we don't have city, try to extract from full_name or use abbreviation
                mapped_df['city'] = None
            if 'name' in df.columns:
                mapped_df['name'] = df['name']
            elif 'nickname' in df.columns:
                mapped_df['name'] = df['nickname']
            # conference and division are not in CSV, leave as NULL
        
        elif table_name == 'players':
            # Map player.csv or common_player_info.csv columns to players table
            if 'id' in df.columns:
                mapped_df['id'] = pd.to_numeric(df['id'], errors='coerce').fillna(0).astype(int)
            elif 'person_id' in df.columns:
                # common_player_info.csv uses person_id
                mapped_df['id'] = pd.to_numeric(df['person_id'], errors='coerce').fillna(0).astype(int)
            
            if 'first_name' in df.columns:
                mapped_df['first_name'] = df['first_name']
            if 'last_name' in df.columns:
                mapped_df['last_name'] = df['last_name']
            
            # Additional fields from common_player_info.csv
            if 'height' in df.columns:
                mapped_df['height'] = df['height']
            if 'weight' in df.columns:
                mapped_df['weight'] = pd.to_numeric(df['weight'], errors='coerce').fillna(0).astype(int)
            if 'birthdate' in df.columns:
                mapped_df['birth_date'] = pd.to_datetime(df['birthdate'], errors='coerce').dt.date
            if 'country' in df.columns:
                mapped_df['country'] = df['country']
        
        elif table_name == 'games':
            # Get valid team IDs from database to filter games BEFORE mapping
            original_len = len(df)
            if engine and 'team_id_home' in df.columns and 'team_id_away' in df.columns:
                try:
                    # Get list of valid team IDs from teams table
                    valid_teams = pd.read_sql("SELECT id FROM teams", engine)['id'].tolist()
                    # Filter to only games where both teams exist
                    df = df[df['team_id_home'].isin(valid_teams) & df['team_id_away'].isin(valid_teams)]
                    if len(df) < original_len:
                        logger.info(f"   Filtered games: {len(df)} valid games out of {original_len} total")
                except Exception as e:
                    logger.warning(f"   Could not filter by valid teams: {e}")
            
            # Now map the filtered data
            if 'game_id' in df.columns:
                # Convert game_id string (like "0024600001") to integer
                # Remove leading zeros for MySQL INT storage
                mapped_df['id'] = pd.to_numeric(df['game_id'], errors='coerce').fillna(0).astype(int)
            elif 'id' in df.columns:
                mapped_df['id'] = pd.to_numeric(df['id'], errors='coerce').fillna(0).astype(int)
            
            if 'game_date' in df.columns:
                mapped_df['game_date'] = pd.to_datetime(df['game_date'], errors='coerce').dt.date
            
            if 'team_id_home' in df.columns:
                mapped_df['home_team_id'] = pd.to_numeric(df['team_id_home'], errors='coerce').fillna(0).astype(int)
            if 'team_id_away' in df.columns:
                mapped_df['away_team_id'] = pd.to_numeric(df['team_id_away'], errors='coerce').fillna(0).astype(int)
            
            if 'pts_home' in df.columns:
                mapped_df['home_score'] = pd.to_numeric(df['pts_home'], errors='coerce').fillna(0).astype(int)
            if 'pts_away' in df.columns:
                mapped_df['away_score'] = pd.to_numeric(df['pts_away'], errors='coerce').fillna(0).astype(int)
            
            if 'wl_home' in df.columns:
                mapped_df['status'] = df['wl_home'].apply(lambda x: 'FINAL' if pd.notna(x) and x in ['W', 'L'] else 'SCHEDULED')
            else:
                mapped_df['status'] = 'FINAL'
            
            if 'season_type' in df.columns:
                mapped_df['game_type'] = df['season_type']
            elif 'season_id' in df.columns:
                # Extract season from season_id if available
                mapped_df['season'] = df['season_id'].astype(str)
                mapped_df['game_type'] = 'REGULAR'
            else:
                mapped_df['game_type'] = 'REGULAR'
        
        return mapped_df
    
    def clean_data(self, df: pd.DataFrame, table_name: str) -> pd.DataFrame:
        """
        Clean and prepare data for import
        
        Args:
            df: DataFrame to clean
            table_name: Target table name for table-specific cleaning
        
        Returns:
            pd.DataFrame: Cleaned DataFrame
        """
        # Map CSV columns to schema first
        df = self.map_csv_to_schema(df, table_name, self.engine)
        
        if df.empty:
            logger.warning(f"⚠️ No data mapped for {table_name}")
            return df
        
        # Remove duplicates based on primary key
        if 'id' in df.columns:
            df = df.drop_duplicates(subset=['id'], keep='last')
        
        # Handle missing values - don't fill with empty string for numeric columns
        for col in df.columns:
            if df[col].dtype in ['int64', 'float64']:
                df[col] = df[col].fillna(0)
            elif df[col].dtype == 'object':
                df[col] = df[col].fillna('')
        
        # Table-specific cleaning
        if table_name == 'players':
            # Ensure position values are valid if column exists
            if 'position' in df.columns:
                valid_positions = ['PG', 'SG', 'SF', 'PF', 'C']
                df['position'] = df['position'].apply(
                    lambda x: x if x in valid_positions else None
                )
        
        return df
    
    def validate_import(self, table_name: str) -> Dict[str, int]:
        """
        Validate imported data
        
        Args:
            table_name: Table name to validate
        
        Returns:
            Dict with validation results
        """
        try:
            query = f"SELECT COUNT(*) as row_count FROM {table_name}"
            result = pd.read_sql(query, self.engine)
            row_count = result['row_count'].iloc[0]
            
            logger.info(f"✅ {table_name}: {row_count} rows imported")
            return {'table': table_name, 'rows': row_count}
            
        except Exception as e:
            logger.error(f"❌ Error validating {table_name}: {e}")
            return {'table': table_name, 'rows': 0, 'error': str(e)}
    
    def import_all_data(self, data_directory: str) -> bool:
        """
        Import all NBA data from CSV files
        
        Args:
            data_directory: Directory containing CSV files
        
        Returns:
            bool: True if all imports successful
        """
        if not self.connect():
            return False
        
        # Define import order and file mappings
        # Only import files that exist and have data mapping support
        import_order = [
            # Core tables
            ('team.csv', 'teams'),
            ('player.csv', 'players'),
            ('game.csv', 'games'),
            # Enrichment data
            ('common_player_info.csv', 'players'),  # Update players with additional info
            # Note: The following tables don't have direct CSV mappings:
            # - player_game_logs: Will come from API
            # - injuries: Will come from API
            # - dfs_projections: Will come from API
            # - daily_dfs_data: Will come from API
            # - game_lineups: Will come from API
        ]
        
        # Check which tables already have data
        from sqlalchemy import inspect
        inspector = inspect(self.engine)
        existing_tables = inspector.get_table_names()
        
        # Filter and handle updates vs inserts
        filtered_order = []
        for csv_file, table_name in import_order:
            csv_path = os.path.join(data_directory, csv_file)
            if not os.path.exists(csv_path):
                logger.warning(f"⚠️ CSV file not found: {csv_path}")
                continue
                
            if table_name in existing_tables:
                # Check if table has data
                result = pd.read_sql(f"SELECT COUNT(*) as cnt FROM {table_name}", self.engine)
                count = result['cnt'].iloc[0]
                
                # For players table, allow updates from common_player_info.csv
                if table_name == 'players' and csv_file == 'common_player_info.csv':
                    if count > 0:
                        logger.info(f"📝 Will update existing players with data from {csv_file}")
                        filtered_order.append((csv_file, table_name))
                    else:
                        logger.warning(f"⚠️ Cannot update {table_name} - no existing data")
                elif count == 0:
                    filtered_order.append((csv_file, table_name))
                else:
                    logger.info(f"⏭️ Skipping {csv_file} - {table_name} already has {count} rows")
            else:
                filtered_order.append((csv_file, table_name))
        
        import_order = filtered_order
        
        success_count = 0
        total_files = len(import_order)
        
        logger.info(f"🚀 Starting import of {total_files} CSV files...")
        
        for csv_file, table_name in import_order:
            csv_path = os.path.join(data_directory, csv_file)
            
            if os.path.exists(csv_path):
                if self.import_csv_file(csv_path, table_name):
                    self.validate_import(table_name)
                    success_count += 1
                else:
                    logger.error(f"❌ Failed to import {csv_file}")
            else:
                logger.warning(f"⚠️ CSV file not found: {csv_path}")
        
        logger.info(f"📊 Import Summary: {success_count}/{total_files} files imported successfully")
        return success_count == total_files

def main():
    """Main function to run the import process"""
    
    # MySQL HeatWave configuration - prefer HEATWAVE_ vars, fallback to MYSQL_
    mysql_config = {
        'host': os.getenv('HEATWAVE_HOST') or os.getenv('MYSQL_HOST', 'localhost'),
        'port': int(os.getenv('HEATWAVE_PORT') or os.getenv('MYSQL_PORT', '3306')),
        'user': os.getenv('HEATWAVE_USER') or os.getenv('MYSQL_USER', 'root'),
        'password': os.getenv('HEATWAVE_PASSWORD') or os.getenv('MYSQL_PASSWORD', ''),
        'database': os.getenv('HEATWAVE_DATABASE') or os.getenv('MYSQL_DATABASE', 'nba_fantasy')
    }
    
    # Data directory
    data_directory = os.getenv('HISTORICAL_DATA_PATH') or os.getenv('NBA_DATA_DIRECTORY', './historical_data')
    
    logger.info("🏀 NBA Fantasy Data Importer")
    logger.info(f"📁 Data directory: {data_directory}")
    logger.info(f"🗄️ MySQL host: {mysql_config['host']}:{mysql_config['port']}")
    logger.info(f"📊 Database: {mysql_config['database']}")
    
    # Create importer
    importer = NBAFantasyDataImporter(mysql_config)
    
    # Import all data
    success = importer.import_all_data(data_directory)
    
    if success:
        logger.info("🎉 All data imported successfully!")
        return 0
    else:
        logger.error("❌ Some imports failed. Check logs for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
