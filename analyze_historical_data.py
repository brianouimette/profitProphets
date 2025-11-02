#!/usr/bin/env python3
"""
Historical Data Analysis Script
Analyzes the 4.66GB historical data to understand structure and quality
"""

import sys
import os
from pathlib import Path
from ml_service.data_analyzer import analyze_historical_data

def main():
    """Main function to analyze historical data"""
    print("🔍 NBA Fantasy Optimizer - Historical Data Analysis")
    print("=" * 60)
    
    # Get data path from user
    if len(sys.argv) > 1:
        data_path = sys.argv[1]
    else:
        data_path = input("Enter path to your historical data (4.66GB): ").strip()
        if not data_path:
            print("❌ No data path provided")
            return
    
    # Check if path exists
    if not Path(data_path).exists():
        print(f"❌ Path does not exist: {data_path}")
        return
    
    print(f"📁 Analyzing data at: {data_path}")
    print("⏳ This may take a few minutes for large datasets...")
    
    try:
        # Run the analysis
        report = analyze_historical_data(data_path)
        
        # Display key findings
        print("\n📊 Analysis Results:")
        print("=" * 40)
        
        structure = report['data_structure']
        print(f"📁 Total Size: {structure['total_size_gb']} GB")
        print(f"📄 Files Found: {len(structure['files'])}")
        print(f"🔧 File Types: {list(structure['file_types'].keys())}")
        
        csv_analysis = report['csv_analysis']
        print(f"📊 CSV Files: {len(csv_analysis['csv_files'])}")
        print(f"📈 Total Records: {csv_analysis['total_records']:,}")
        
        mapping = report['mapping_strategy']
        print(f"🔗 Mapping Strategy: {mapping['recommended_approach']}")
        print(f"🎯 Confidence Level: {mapping['confidence_level']}")
        
        # Show recommendations
        if report['recommendations']:
            print("\n💡 Recommendations:")
            for rec in report['recommendations']:
                print(f"   • {rec}")
        
        # Show next steps
        if report['next_steps']:
            print("\n🚀 Next Steps:")
            for step in report['next_steps']:
                print(f"   • {step}")
        
        print(f"\n📄 Full report saved to: historical_data_analysis.json")
        print("✅ Analysis complete!")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
