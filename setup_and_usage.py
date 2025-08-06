#!/usr/bin/env python3
"""
Setup and Usage Guide for Disease Prediction Database System
"""
import os
from pathlib import Path
from database_manager import DiseaseDataDatabase

def setup_database():
    """Set up the database with all GeoJSON data"""
    print("🚀 Setting up Disease Prediction Database System\n")
    
    print("Step 1: Creating database schema...")
    db = DiseaseDataDatabase()
    db.create_database_schema()
    print("✅ Database schema created")
    
    print("\nStep 2: Importing GeoJSON files...")
    print("⏳ This will take several minutes for 273 files...")
    db.import_geojson_files()
    print("✅ Data import completed")
    
    print("\nStep 3: Verifying import...")
    stats = db.get_database_stats()
    print(f"📊 Database Statistics:")
    print(f"  - Total predictions: {stats['total_predictions']:,}")
    print(f"  - Total dates: {stats['total_dates']}")
    print(f"  - Total regions: {stats['total_regions']}")
    print(f"  - Date range: {stats['date_range'][0]} to {stats['date_range'][1]}")
    
    print("\n🎉 Setup complete! You can now start the web application.")

def show_usage_guide():
    """Show usage guide for the system"""
    print("""
🎯 Disease Prediction Database System - Usage Guide
=================================================

📁 Project Structure:
├── data/                           # Individual GeoJSON files by date  
├── output/
│   ├── database/                   # SQLite database files
│   └── geojson_by_date/           # Alternative split files
├── src/main/python/
│   ├── database_manager.py        # Database operations
│   ├── app.py                     # Flask web application
│   └── test_database.py          # Database testing
└── src/main/resources/
    ├── index.html                 # Web interface
    └── assets/map.js              # Map visualization

🚀 Getting Started:
1. Set up database:     python setup_and_usage.py --setup
2. Test database:       python src/main/python/test_database.py  
3. Start web app:       python src/main/python/app.py
4. Open browser:        http://localhost:5000

🔧 API Endpoints:
- GET /api/dates                   # Get all available dates
- GET /api/data?date=YYYY-MM-DD   # Get predictions for specific date
- GET /api/region/<townvill>      # Get timeline for specific region
- GET /api/high-risk?date=YYYY-MM-DD&threshold=50  # Get high-risk regions
- GET /api/summary/<date>         # Get daily summary statistics
- GET /api/stats                  # Get overall database statistics

📊 Database Features:
- Fast queries with optimized indexes
- 273 days of prediction data
- Regional and temporal analysis
- Risk level categorization
- Daily summary statistics

💡 Usage Examples:
# Get data for specific date
curl "http://localhost:5000/api/data?date=2023-06-01"

# Get high-risk regions  
curl "http://localhost:5000/api/high-risk?date=2023-06-01&threshold=20"

# Get region timeline
curl "http://localhost:5000/api/region/A6727-0001-00?start_date=2023-06-01&end_date=2023-06-07"

🎨 Web Interface Features:
- Interactive map visualization
- Date selector for temporal analysis  
- Region filtering and search
- Risk level color coding
- Statistical dashboard

⚡ Performance Benefits:
- SQLite indexes for fast queries
- Pre-computed daily summaries
- Efficient GeoJSON serving
- Memory-optimized Flask app

🔍 Troubleshooting:
- Database not found: Run setup first
- Empty results: Check date format (YYYY-MM-DD)  
- Slow queries: Database may still be importing
- Web app errors: Check Flask dependencies

📝 Notes:
- Data covers 2023-06-01 to 2024-02-28
- All predictions are for Tainan city regions
- Percentage values represent risk levels
- Binary predictions: 0=low risk, 1=high risk
""")

def main():
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--setup':
        setup_database()
    else:
        show_usage_guide()

if __name__ == "__main__":
    main()