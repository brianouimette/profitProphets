"""
Historical Data Analyzer
Analyzes the 4.66GB historical data to understand structure and quality
"""

import pandas as pd
import numpy as np
import os
import json
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HistoricalDataAnalyzer:
    """Analyzes historical data structure and quality"""
    
    def __init__(self, data_path: str):
        """Initialize with path to historical data"""
        self.data_path = Path(data_path)
        self.analysis_results = {}
        
    def analyze_data_structure(self) -> Dict[str, Any]:
        """Analyze the structure of historical data"""
        logger.info("🔍 Analyzing historical data structure...")
        
        structure_analysis = {
            'data_path': str(self.data_path),
            'exists': self.data_path.exists(),
            'is_directory': self.data_path.is_dir() if self.data_path.exists() else False,
            'total_size_gb': 0,
            'files': [],
            'file_types': {},
            'largest_files': []
        }
        
        if not self.data_path.exists():
            logger.warning(f"❌ Data path does not exist: {self.data_path}")
            return structure_analysis
        
        # Calculate total size
        total_size = 0
        for file_path in self.data_path.rglob('*'):
            if file_path.is_file():
                file_size = file_path.stat().st_size
                total_size += file_size
                
                structure_analysis['files'].append({
                    'path': str(file_path.relative_to(self.data_path)),
                    'size_mb': round(file_size / (1024 * 1024), 2),
                    'extension': file_path.suffix
                })
                
                # Track file types
                ext = file_path.suffix.lower()
                if ext not in structure_analysis['file_types']:
                    structure_analysis['file_types'][ext] = {'count': 0, 'total_size_mb': 0}
                structure_analysis['file_types'][ext]['count'] += 1
                structure_analysis['file_types'][ext]['total_size_mb'] += file_size / (1024 * 1024)
        
        structure_analysis['total_size_gb'] = round(total_size / (1024 * 1024 * 1024), 2)
        
        # Get largest files
        structure_analysis['largest_files'] = sorted(
            structure_analysis['files'], 
            key=lambda x: x['size_mb'], 
            reverse=True
        )[:10]
        
        logger.info(f"📊 Data structure analysis complete:")
        logger.info(f"   Total size: {structure_analysis['total_size_gb']} GB")
        logger.info(f"   Files: {len(structure_analysis['files'])}")
        logger.info(f"   File types: {list(structure_analysis['file_types'].keys())}")
        
        return structure_analysis
    
    def analyze_csv_files(self) -> Dict[str, Any]:
        """Analyze CSV files in the historical data"""
        logger.info("📊 Analyzing CSV files...")
        
        csv_analysis = {
            'csv_files': [],
            'total_records': 0,
            'columns_analysis': {},
            'data_quality_issues': []
        }
        
        csv_files = list(self.data_path.rglob('*.csv'))
        
        for csv_file in csv_files:
            try:
                logger.info(f"   Analyzing: {csv_file.name}")
                
                # Read first few rows to understand structure
                sample_df = pd.read_csv(csv_file, nrows=1000)
                
                file_analysis = {
                    'file_path': str(csv_file.relative_to(self.data_path)),
                    'columns': list(sample_df.columns),
                    'sample_rows': len(sample_df),
                    'dtypes': sample_df.dtypes.to_dict(),
                    'null_counts': sample_df.isnull().sum().to_dict(),
                    'memory_usage_mb': sample_df.memory_usage(deep=True).sum() / (1024 * 1024)
                }
                
                # Try to get full row count (this might be slow for large files)
                try:
                    full_df = pd.read_csv(csv_file)
                    file_analysis['total_rows'] = len(full_df)
                    csv_analysis['total_records'] += len(full_df)
                except Exception as e:
                    logger.warning(f"Could not read full file {csv_file.name}: {e}")
                    file_analysis['total_rows'] = 'Unknown'
                
                csv_analysis['csv_files'].append(file_analysis)
                
                # Analyze columns for potential player/team IDs
                for col in sample_df.columns:
                    if col.lower() in ['player_id', 'team_id', 'id', 'player', 'team']:
                        if col not in csv_analysis['columns_analysis']:
                            csv_analysis['columns_analysis'][col] = {
                                'files': [],
                                'sample_values': [],
                                'unique_count': 0
                            }
                        
                        csv_analysis['columns_analysis'][col]['files'].append(csv_file.name)
                        csv_analysis['columns_analysis'][col]['sample_values'].extend(
                            sample_df[col].dropna().head(10).tolist()
                        )
                
            except Exception as e:
                logger.error(f"Error analyzing {csv_file.name}: {e}")
                csv_analysis['data_quality_issues'].append({
                    'file': str(csv_file.relative_to(self.data_path)),
                    'error': str(e)
                })
        
        logger.info(f"📊 CSV analysis complete:")
        logger.info(f"   CSV files found: {len(csv_analysis['csv_files'])}")
        logger.info(f"   Total records: {csv_analysis['total_records']:,}")
        logger.info(f"   Potential ID columns: {list(csv_analysis['columns_analysis'].keys())}")
        
        return csv_analysis
    
    def identify_player_mapping_strategy(self, csv_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Identify strategy for mapping player IDs"""
        logger.info("🔗 Identifying player mapping strategy...")
        
        mapping_strategy = {
            'potential_id_columns': [],
            'mapping_approaches': [],
            'recommended_approach': None,
            'confidence_level': 'low'
        }
        
        # Analyze potential ID columns
        for col, analysis in csv_analysis['columns_analysis'].items():
            if 'id' in col.lower() or col.lower() in ['player', 'team']:
                mapping_strategy['potential_id_columns'].append({
                    'column': col,
                    'files': analysis['files'],
                    'sample_values': analysis['sample_values'][:5],
                    'data_type': type(analysis['sample_values'][0]).__name__ if analysis['sample_values'] else 'unknown'
                })
        
        # Determine mapping approach based on data
        if mapping_strategy['potential_id_columns']:
            mapping_strategy['mapping_approaches'] = [
                'Direct ID matching (if IDs are consistent)',
                'Name-based matching (first_name + last_name)',
                'Jersey number + team matching',
                'External mapping table creation'
            ]
            
            # Check if we have name columns
            name_columns = [col for col in csv_analysis['columns_analysis'].keys() 
                          if any(name in col.lower() for name in ['name', 'first', 'last', 'player'])]
            
            if name_columns:
                mapping_strategy['recommended_approach'] = 'Name-based matching with ID fallback'
                mapping_strategy['confidence_level'] = 'medium'
            else:
                mapping_strategy['recommended_approach'] = 'Direct ID matching'
                mapping_strategy['confidence_level'] = 'high'
        
        logger.info(f"🔗 Mapping strategy identified:")
        logger.info(f"   Recommended approach: {mapping_strategy['recommended_approach']}")
        logger.info(f"   Confidence level: {mapping_strategy['confidence_level']}")
        
        return mapping_strategy
    
    def generate_data_quality_report(self) -> Dict[str, Any]:
        """Generate comprehensive data quality report"""
        logger.info("📋 Generating data quality report...")
        
        # Run all analyses
        structure = self.analyze_data_structure()
        csv_analysis = self.analyze_csv_files()
        mapping_strategy = self.identify_player_mapping_strategy(csv_analysis)
        
        quality_report = {
            'data_structure': structure,
            'csv_analysis': csv_analysis,
            'mapping_strategy': mapping_strategy,
            'recommendations': [],
            'next_steps': []
        }
        
        # Generate recommendations
        if structure['total_size_gb'] > 4:
            quality_report['recommendations'].append("Large dataset detected - consider data partitioning")
        
        if csv_analysis['data_quality_issues']:
            quality_report['recommendations'].append("Data quality issues found - review error logs")
        
        if mapping_strategy['confidence_level'] == 'low':
            quality_report['recommendations'].append("Low confidence in ID mapping - manual review required")
        
        # Generate next steps
        quality_report['next_steps'] = [
            "Create player ID mapping table",
            "Validate data quality for key columns",
            "Set up data ingestion pipeline",
            "Build data validation rules"
        ]
        
        logger.info("📋 Data quality report generated successfully")
        
        return quality_report
    
    def save_analysis_report(self, report: Dict[str, Any], output_path: str = "historical_data_analysis.json"):
        """Save analysis report to file"""
        try:
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            logger.info(f"📄 Analysis report saved to: {output_path}")
        except Exception as e:
            logger.error(f"Error saving analysis report: {e}")

def analyze_historical_data(data_path: str) -> Dict[str, Any]:
    """Main function to analyze historical data"""
    analyzer = HistoricalDataAnalyzer(data_path)
    report = analyzer.generate_data_quality_report()
    analyzer.save_analysis_report(report)
    return report

if __name__ == "__main__":
    # Example usage
    data_path = input("Enter path to historical data: ").strip()
    if not data_path:
        data_path = "./historical_data"
    
    report = analyze_historical_data(data_path)
    print(f"Analysis complete! Report saved to: historical_data_analysis.json")
