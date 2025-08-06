#!/usr/bin/env python3
"""
SQLite Database Manager for Disease Prediction Data
Handles import from multiple GeoJSON files and provides fast query interface
"""
import sqlite3
import json
from pathlib import Path
from datetime import datetime
import glob
from collections import defaultdict
import os

class DiseaseDataDatabase:
    def __init__(self, db_path="output/database/disease_predictions.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
    def create_database_schema(self):
        """Create optimized SQLite schema for fast queries"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Drop existing tables if they exist
        cursor.execute("DROP TABLE IF EXISTS predictions")
        cursor.execute("DROP TABLE IF EXISTS daily_summary")
        cursor.execute("DROP TABLE IF EXISTS region_info")
        
        # Main predictions table
        cursor.execute('''
            CREATE TABLE predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                townvill TEXT NOT NULL,
                town TEXT NOT NULL,
                county TEXT NOT NULL,
                case_lag_future_14 INTEGER DEFAULT 0,
                predicted_case_lag_future_14 REAL NOT NULL,
                predicted_case_lag_future_14_binary INTEGER NOT NULL,
                predicted_case_lag_future_14_percentage REAL NOT NULL,
                x_coord REAL,
                y_coord REAL,
                area REAL,
                geometry_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Region information table (static data)
        cursor.execute('''
            CREATE TABLE region_info (
                townvill TEXT PRIMARY KEY,
                code1 TEXT,
                code2 TEXT,
                town_id TEXT,
                town TEXT,
                county_id TEXT,
                county TEXT,
                x_coord REAL,
                y_coord REAL,
                area REAL,
                geometry_json TEXT
            )
        ''')
        
        # Daily summary statistics
        cursor.execute('''
            CREATE TABLE daily_summary (
                date TEXT PRIMARY KEY,
                total_regions INTEGER,
                total_predicted_cases REAL,
                avg_prediction REAL,
                max_prediction REAL,
                min_prediction REAL,
                high_risk_regions INTEGER,
                medium_risk_regions INTEGER,
                low_risk_regions INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes for fast queries
        cursor.execute('CREATE INDEX idx_predictions_date ON predictions(date)')
        cursor.execute('CREATE INDEX idx_predictions_town ON predictions(town)')
        cursor.execute('CREATE INDEX idx_predictions_townvill ON predictions(townvill)')
        cursor.execute('CREATE INDEX idx_predictions_date_town ON predictions(date, town)')
        cursor.execute('CREATE INDEX idx_predictions_date_townvill ON predictions(date, townvill)')
        cursor.execute('CREATE INDEX idx_predictions_binary ON predictions(predicted_case_lag_future_14_binary)')
        cursor.execute('CREATE INDEX idx_predictions_percentage ON predictions(predicted_case_lag_future_14_percentage)')
        
        conn.commit()
        conn.close()
        
        print(f"Database schema created: {self.db_path}")
    
    def import_geojson_files(self, data_dir="data"):
        """Import all GeoJSON files from data directory"""
        data_path = Path(data_dir)
        geojson_files = list(data_path.glob("*_case_results.geojson"))
        
        if not geojson_files:
            print(f"No GeoJSON files found in {data_path}")
            return
        
        print(f"Found {len(geojson_files)} GeoJSON files to import")
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Prepare batch data
        prediction_records = []
        region_records = {}
        daily_stats = defaultdict(lambda: {
            'count': 0, 'predictions': [], 'binary_counts': [0, 0, 0]
        })
        
        for file_path in sorted(geojson_files):
            print(f"Processing {file_path.name}...")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for feature in data['features']:
                props = feature['properties']
                geom_json = json.dumps(feature['geometry'], separators=(',', ':'))
                
                # Extract date from filename or properties
                date = props.get('date', file_path.stem.split('_')[0])
                
                # Prediction record
                prediction_record = (
                    date,
                    props['townvill'],
                    props['TOWN'],
                    props.get('COUNTY', '臺南市'),  # Default to Tainan
                    props.get('case_lag_future_14', 0),
                    props['predicted_case_lag_future_14'],
                    props['predicted_case_lag_future_14_binary'],
                    props['predicted_case_lag_future_14_percentage'],
                    props.get('X', 0),
                    props.get('Y', 0),
                    props.get('AREA', 0),
                    geom_json
                )
                prediction_records.append(prediction_record)
                
                # Region info (unique regions only)
                townvill = props['townvill']
                if townvill not in region_records:
                    region_records[townvill] = (
                        townvill,
                        props.get('CODE1', ''),
                        props.get('CODE2', ''),
                        props.get('TOWN_ID', ''),
                        props['TOWN'],
                        props.get('COUNTY_ID', ''),
                        props.get('COUNTY', '臺南市'),
                        props.get('X', 0),
                        props.get('Y', 0),
                        props.get('AREA', 0),
                        geom_json
                    )
                
                # Daily statistics
                pred_val = props['predicted_case_lag_future_14']
                pred_percentage = props['predicted_case_lag_future_14_percentage']
                
                daily_stats[date]['count'] += 1
                daily_stats[date]['predictions'].append(pred_val)
                
                # Risk categorization based on percentage
                if pred_percentage >= 50:
                    daily_stats[date]['binary_counts'][2] += 1  # High risk
                elif pred_percentage >= 20:
                    daily_stats[date]['binary_counts'][1] += 1  # Medium risk
                else:
                    daily_stats[date]['binary_counts'][0] += 1  # Low risk
        
        print(f"Importing {len(prediction_records)} prediction records...")
        
        # Batch insert predictions
        cursor.executemany('''
            INSERT INTO predictions 
            (date, townvill, town, county, case_lag_future_14, 
             predicted_case_lag_future_14, predicted_case_lag_future_14_binary,
             predicted_case_lag_future_14_percentage, x_coord, y_coord, area, geometry_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', prediction_records)
        
        print(f"Importing {len(region_records)} unique regions...")
        
        # Insert unique regions
        cursor.executemany('''
            INSERT OR REPLACE INTO region_info 
            (townvill, code1, code2, town_id, town, county_id, county, 
             x_coord, y_coord, area, geometry_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', list(region_records.values()))
        
        # Insert daily summaries
        summary_records = []
        for date, stats in daily_stats.items():
            preds = stats['predictions']
            if preds:
                summary_records.append((
                    date,
                    stats['count'],
                    sum(preds),
                    sum(preds) / len(preds),
                    max(preds),
                    min(preds),
                    stats['binary_counts'][2],  # High risk
                    stats['binary_counts'][1],  # Medium risk
                    stats['binary_counts'][0]   # Low risk
                ))
        
        print(f"Importing {len(summary_records)} daily summaries...")
        
        cursor.executemany('''
            INSERT INTO daily_summary 
            (date, total_regions, total_predicted_cases, avg_prediction, 
             max_prediction, min_prediction, high_risk_regions, 
             medium_risk_regions, low_risk_regions)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', summary_records)
        
        conn.commit()
        conn.close()
        
        print(f"✅ Import complete!")
        print(f"- Predictions: {len(prediction_records)}")
        print(f"- Unique regions: {len(region_records)}")  
        print(f"- Date range: {len(daily_stats)} days")
    
    def get_predictions_by_date(self, date):
        """Get all predictions for a specific date"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT date, townvill, town, predicted_case_lag_future_14,
                   predicted_case_lag_future_14_percentage, geometry_json
            FROM predictions 
            WHERE date = ?
            ORDER BY predicted_case_lag_future_14_percentage DESC
        ''', (date,))
        
        results = cursor.fetchall()
        conn.close()
        
        return results
    
    def get_predictions_by_region(self, townvill, start_date=None, end_date=None):
        """Get predictions for a specific region with optional date range"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        if start_date and end_date:
            cursor.execute('''
                SELECT date, predicted_case_lag_future_14, 
                       predicted_case_lag_future_14_percentage
                FROM predictions 
                WHERE townvill = ? AND date BETWEEN ? AND ?
                ORDER BY date
            ''', (townvill, start_date, end_date))
        else:
            cursor.execute('''
                SELECT date, predicted_case_lag_future_14,
                       predicted_case_lag_future_14_percentage  
                FROM predictions
                WHERE townvill = ?
                ORDER BY date
            ''', (townvill,))
        
        results = cursor.fetchall()
        conn.close()
        
        return results
    
    def get_high_risk_regions(self, date, threshold=50):
        """Get high-risk regions for a specific date"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT townvill, town, predicted_case_lag_future_14_percentage,
                   geometry_json
            FROM predictions 
            WHERE date = ? AND predicted_case_lag_future_14_percentage >= ?
            ORDER BY predicted_case_lag_future_14_percentage DESC
        ''', (date, threshold))
        
        results = cursor.fetchall()
        conn.close()
        
        return results
    
    def get_daily_summary(self, date):
        """Get daily summary statistics"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM daily_summary WHERE date = ?
        ''', (date,))
        
        result = cursor.fetchone()
        conn.close()
        
        return result
    
    def get_available_dates(self):
        """Get all available dates in the database"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('SELECT DISTINCT date FROM predictions ORDER BY date')
        results = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        return results
    
    def get_database_stats(self):
        """Get database statistics"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM predictions')
        total_predictions = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT date) FROM predictions')
        total_dates = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT townvill) FROM predictions')
        total_regions = cursor.fetchone()[0]
        
        cursor.execute('SELECT MIN(date), MAX(date) FROM predictions')
        date_range = cursor.fetchone()
        
        conn.close()
        
        return {
            'total_predictions': total_predictions,
            'total_dates': total_dates,
            'total_regions': total_regions,
            'date_range': date_range
        }

def main():
    """Example usage"""
    db = DiseaseDataDatabase()
    
    # Create database schema
    db.create_database_schema()
    
    # Import all GeoJSON files
    db.import_geojson_files()
    
    # Show database stats
    stats = db.get_database_stats()
    print(f"\n📊 Database Statistics:")
    print(f"Total predictions: {stats['total_predictions']:,}")
    print(f"Total dates: {stats['total_dates']}")
    print(f"Total regions: {stats['total_regions']}")
    print(f"Date range: {stats['date_range'][0]} to {stats['date_range'][1]}")

if __name__ == "__main__":
    main()