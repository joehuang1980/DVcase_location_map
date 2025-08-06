#!/usr/bin/env python3
"""
Data processor for splitting GeoJSON by date and creating database
"""
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import os

class DiseaseDataProcessor:
    def __init__(self, geojson_path, output_dir="output"):
        self.geojson_path = Path(geojson_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        (self.output_dir / "geojson_by_date").mkdir(exist_ok=True)
        (self.output_dir / "database").mkdir(exist_ok=True)
    
    def split_geojson_by_date(self):
        """Split GeoJSON file by date into separate files"""
        print("Loading GeoJSON data...")
        with open(self.geojson_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Group features by date
        features_by_date = defaultdict(list)
        
        for feature in data['features']:
            date = feature['properties']['date']
            features_by_date[date].append(feature)
        
        print(f"Found {len(features_by_date)} unique dates")
        
        # Save each date as separate GeoJSON file
        for date, features in features_by_date.items():
            date_geojson = {
                "type": "FeatureCollection",
                "features": features
            }
            
            # Format filename
            date_str = date.replace('-', '')
            filename = f"{date_str}_predictions.geojson"
            filepath = self.output_dir / "geojson_by_date" / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(date_geojson, f, ensure_ascii=False)
            
            print(f"Saved {len(features)} features for {date} to {filename}")
        
        return list(features_by_date.keys())
    
    def create_database(self):
        """Create SQLite database with optimized schema"""
        db_path = self.output_dir / "database" / "disease_predictions.db"
        
        # Remove existing database
        if db_path.exists():
            db_path.unlink()
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create main predictions table with indexes
        cursor.execute('''
            CREATE TABLE predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                townvill TEXT NOT NULL,
                town TEXT NOT NULL,
                county TEXT NOT NULL,
                case_lag_future_14 INTEGER,
                predicted_case_lag_future_14 REAL,
                predicted_case_lag_future_14_binary INTEGER,
                predicted_case_lag_future_14_percentage REAL,
                geometry_json TEXT,
                x_coord REAL,
                y_coord REAL,
                area REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes for fast queries
        cursor.execute('CREATE INDEX idx_date ON predictions(date)')
        cursor.execute('CREATE INDEX idx_town ON predictions(town)')
        cursor.execute('CREATE INDEX idx_townvill ON predictions(townvill)')
        cursor.execute('CREATE INDEX idx_date_town ON predictions(date, town)')
        cursor.execute('CREATE INDEX idx_date_townvill ON predictions(date, townvill)')
        
        # Create summary table for quick statistics
        cursor.execute('''
            CREATE TABLE daily_summary (
                date TEXT PRIMARY KEY,
                total_regions INTEGER,
                avg_prediction REAL,
                max_prediction REAL,
                high_risk_regions INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        
        print(f"Database created: {db_path}")
        return db_path
    
    def import_data_to_database(self):
        """Import GeoJSON data to SQLite database"""
        db_path = self.output_dir / "database" / "disease_predictions.db"
        
        print("Loading GeoJSON data for database import...")
        with open(self.geojson_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"Importing {len(data['features'])} records...")
        
        # Prepare data for batch insert
        records = []
        daily_stats = defaultdict(lambda: {'count': 0, 'predictions': [], 'high_risk': 0})
        
        for feature in data['features']:
            props = feature['properties']
            geom_json = json.dumps(feature['geometry'])
            
            record = (
                props['date'],
                props['townvill'],
                props['TOWN'],
                props['COUNTY'],
                props.get('case_lag_future_14', 0),
                props['predicted_case_lag_future_14'],
                props['predicted_case_lag_future_14_binary'],
                props['predicted_case_lag_future_14_percentage'],
                geom_json,
                props['X'],
                props['Y'],
                props['AREA']
            )
            records.append(record)
            
            # Calculate daily statistics
            date = props['date']
            pred_val = props['predicted_case_lag_future_14']
            daily_stats[date]['count'] += 1
            daily_stats[date]['predictions'].append(pred_val)
            if props['predicted_case_lag_future_14_binary'] == 1:
                daily_stats[date]['high_risk'] += 1
        
        # Batch insert predictions
        cursor.executemany('''
            INSERT INTO predictions 
            (date, townvill, town, county, case_lag_future_14, 
             predicted_case_lag_future_14, predicted_case_lag_future_14_binary,
             predicted_case_lag_future_14_percentage, geometry_json, x_coord, y_coord, area)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', records)
        
        # Insert daily summaries
        summary_records = []
        for date, stats in daily_stats.items():
            preds = stats['predictions']
            summary_records.append((
                date,
                stats['count'],
                sum(preds) / len(preds),
                max(preds),
                stats['high_risk']
            ))
        
        cursor.executemany('''
            INSERT INTO daily_summary (date, total_regions, avg_prediction, max_prediction, high_risk_regions)
            VALUES (?, ?, ?, ?, ?)
        ''', summary_records)
        
        conn.commit()
        conn.close()
        
        print(f"Imported {len(records)} prediction records")
        print(f"Created {len(summary_records)} daily summaries")
    
    def process_all(self):
        """Run complete data processing pipeline"""
        print("Starting data processing pipeline...")
        
        # Step 1: Split by date
        dates = self.split_geojson_by_date()
        
        # Step 2: Create database
        db_path = self.create_database()
        
        # Step 3: Import data
        self.import_data_to_database()
        
        print("\nData processing complete!")
        print(f"- Split into {len(dates)} date files")
        print(f"- Database: {db_path}")
        print(f"- Date range: {min(dates)} to {max(dates)}")
        
        return db_path

if __name__ == "__main__":
    processor = DiseaseDataProcessor(
        "/home/joe/Documents/2023_semi_supervised_learning/台南未來病例預測模型/病例結果呈現/20250804xgboost_future14_case_results.geojson"
    )
    processor.process_all()