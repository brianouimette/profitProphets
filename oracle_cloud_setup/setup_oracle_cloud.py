#!/usr/bin/env python3
"""
Oracle Cloud Setup Script
Complete setup for NBA Fantasy Optimizer on Oracle Cloud
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OracleCloudSetup:
    """Setup Oracle Cloud infrastructure for NBA Fantasy Optimizer"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.oracle_setup_dir = Path(__file__).parent
        
    def check_dependencies(self) -> bool:
        """Check if required dependencies are installed"""
        logger.info("🔍 Checking dependencies...")
        
        required_packages = [
            'mysql-connector-python',
            'pandas',
            'sqlalchemy',
            'python-dotenv',
            'scikit-learn',
            'fastapi',
            'uvicorn'
        ]
        
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
                logger.info(f"✅ {package}")
            except ImportError:
                missing_packages.append(package)
                logger.warning(f"❌ {package}")
        
        if missing_packages:
            logger.error(f"Missing packages: {missing_packages}")
            logger.info("Install with: pip install " + " ".join(missing_packages))
            return False
        
        logger.info("✅ All dependencies installed")
        return True
    
    def create_directories(self) -> bool:
        """Create necessary directories"""
        logger.info("📁 Creating directories...")
        
        directories = [
            'oracle_cloud_setup',
            'ml_models',
            'historical_data',
            'logs'
        ]
        
        for directory in directories:
            dir_path = self.project_root / directory
            dir_path.mkdir(exist_ok=True)
            logger.info(f"✅ Created: {directory}")
        
        return True
    
    def setup_environment(self) -> bool:
        """Setup environment configuration"""
        logger.info("⚙️ Setting up environment...")
        
        env_file = self.project_root / '.env'
        env_example = self.oracle_setup_dir / 'env_example.txt'
        
        if not env_file.exists():
            if env_example.exists():
                # Copy example to .env
                with open(env_example, 'r') as f:
                    content = f.read()
                
                with open(env_file, 'w') as f:
                    f.write(content)
                
                logger.info("✅ Created .env file from example")
                logger.warning("⚠️ Please update .env with your Oracle Cloud credentials")
            else:
                logger.error("❌ No environment example found")
                return False
        else:
            logger.info("✅ .env file already exists")
        
        return True
    
    def setup_database_schema(self) -> bool:
        """Setup MySQL HeatWave database schema"""
        logger.info("🗄️ Setting up database schema...")
        
        schema_file = self.oracle_setup_dir / 'mysql_schema.sql'
        
        if not schema_file.exists():
            logger.error(f"❌ Schema file not found: {schema_file}")
            return False
        
        logger.info("✅ Database schema file ready")
        logger.info("📋 To setup database, run:")
        logger.info(f"   mysql -h your-heatwave-endpoint -u your-username -p < {schema_file}")
        
        return True
    
    def setup_csv_import(self) -> bool:
        """Setup CSV import functionality"""
        logger.info("📊 Setting up CSV import...")
        
        import_script = self.oracle_setup_dir / 'csv_import.py'
        
        if not import_script.exists():
            logger.error(f"❌ Import script not found: {import_script}")
            return False
        
        # Make script executable
        import_script.chmod(0o755)
        logger.info("✅ CSV import script ready")
        
        return True
    
    def setup_ml_models(self) -> bool:
        """Setup ML models with HeatWave integration"""
        logger.info("🧠 Setting up ML models...")
        
        ml_analyzer = self.project_root / 'ml_service' / 'heatwave_ml_analyzer.py'
        
        if not ml_analyzer.exists():
            logger.error(f"❌ ML analyzer not found: {ml_analyzer}")
            return False
        
        logger.info("✅ HeatWave ML analyzer ready")
        
        return True
    
    def create_setup_instructions(self) -> bool:
        """Create setup instructions"""
        logger.info("📝 Creating setup instructions...")
        
        instructions = """
# Oracle Cloud NBA Fantasy Optimizer Setup Instructions

## Prerequisites
1. Oracle Cloud account with MySQL HeatWave instance
2. Python 3.8+ with required packages
3. Historical NBA data in CSV format

## Setup Steps

### 1. Configure Environment
```bash
# Copy environment template
cp oracle_cloud_setup/env_example.txt .env

# Edit .env with your Oracle Cloud credentials
nano .env
```

### 2. Setup Database Schema
```bash
# Connect to your HeatWave instance and run schema
mysql -h your-heatwave-endpoint -u your-username -p < oracle_cloud_setup/mysql_schema.sql
```

### 3. Import Historical Data
```bash
# Place your CSV files in historical_data/ directory
# Then run the import script
python oracle_cloud_setup/csv_import.py
```

### 4. Test ML Models
```bash
# Test the HeatWave ML analyzer
python ml_service/heatwave_ml_analyzer.py
```

### 5. Start ML Service
```bash
# Start the FastAPI ML service
cd ml_service
uvicorn api:app --host 0.0.0.0 --port 8001
```

## File Structure
```
oracle_cloud_setup/
├── mysql_schema.sql          # Database schema
├── csv_import.py             # CSV import script
├── setup_oracle_cloud.py     # This setup script
└── env_example.txt           # Environment template

ml_service/
├── heatwave_ml_analyzer.py   # HeatWave ML integration
├── api.py                    # FastAPI service
└── ...                       # Other ML modules

historical_data/              # Your NBA CSV files
├── teams.csv
├── players.csv
├── games.csv
├── player_game_logs.csv
├── injuries.csv
├── dfs_projections.csv
└── daily_dfs_data.csv
```

## Next Steps
1. Update .env with your Oracle Cloud credentials
2. Run database schema setup
3. Import your historical data
4. Test the ML models
5. Deploy to Oracle Cloud compute instances

## Troubleshooting
- Check Oracle Cloud security groups for database access
- Verify MySQL HeatWave instance is running
- Ensure CSV files are in correct format
- Check logs for any import errors
"""
        
        instructions_file = self.oracle_setup_dir / 'SETUP_INSTRUCTIONS.md'
        with open(instructions_file, 'w') as f:
            f.write(instructions)
        
        logger.info(f"✅ Setup instructions created: {instructions_file}")
        return True
    
    def run_setup(self) -> bool:
        """Run complete setup process"""
        logger.info("🚀 Starting Oracle Cloud setup...")
        
        steps = [
            ("Check dependencies", self.check_dependencies),
            ("Create directories", self.create_directories),
            ("Setup environment", self.setup_environment),
            ("Setup database schema", self.setup_database_schema),
            ("Setup CSV import", self.setup_csv_import),
            ("Setup ML models", self.setup_ml_models),
            ("Create instructions", self.create_setup_instructions)
        ]
        
        for step_name, step_func in steps:
            logger.info(f"📋 {step_name}...")
            if not step_func():
                logger.error(f"❌ Failed: {step_name}")
                return False
            logger.info(f"✅ Completed: {step_name}")
        
        logger.info("🎉 Oracle Cloud setup completed successfully!")
        logger.info("📝 Next steps:")
        logger.info("   1. Update .env with your Oracle Cloud credentials")
        logger.info("   2. Run database schema setup")
        logger.info("   3. Import your historical data")
        logger.info("   4. Test the ML models")
        
        return True

def main():
    """Main setup function"""
    setup = OracleCloudSetup()
    success = setup.run_setup()
    
    if success:
        logger.info("🎉 Setup completed successfully!")
        return 0
    else:
        logger.error("❌ Setup failed. Check logs for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
