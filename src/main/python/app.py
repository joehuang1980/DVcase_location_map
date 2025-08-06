from flask import Flask, render_template, jsonify, request, send_from_directory
from database_manager import DiseaseDataDatabase
import json
import os
from datetime import datetime

app = Flask(__name__,
            static_folder=os.path.abspath('src/main/resources/assets'),
            template_folder=os.path.abspath('src/main/resources'))

# Initialize database
db = DiseaseDataDatabase()

# Cache available dates for performance
available_dates = None

def get_available_dates():
    """Get available dates with caching"""
    global available_dates
    if available_dates is None:
        available_dates = db.get_available_dates()
    return available_dates

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/dates')
def get_dates():
    """Get all available dates"""
    try:
        dates = get_available_dates()
        return jsonify(dates)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/data')
def get_data_by_date():
    """Get prediction data for a specific date"""
    selected_date = request.args.get('date')
    if not selected_date:
        return jsonify({"error": "Missing date parameter"}), 400
    
    try:
        # Get predictions from database
        predictions = db.get_predictions_by_date(selected_date)
        
        if not predictions:
            return jsonify({"error": "No data found for the specified date"}), 404
        
        # Convert to GeoJSON format
        features = []
        for row in predictions:
            date, townvill, town, predicted_value, predicted_percentage, predicted_binary, actual_case, geometry_json = row
            
            feature = {
                "type": "Feature",
                "properties": {
                    "date": date,
                    "townvill": townvill,
                    "town": town,
                    "predicted_case_lag_future_14": predicted_value,
                    "predicted_case_lag_future_14_percentage": predicted_percentage,
                    "predicted_case_lag_future_14_binary": predicted_binary,
                    "case_lag_future_14": actual_case
                },
                "geometry": json.loads(geometry_json)
            }
            features.append(feature)
        
        geojson = {
            "type": "FeatureCollection",
            "features": features
        }
        
        return jsonify(geojson)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/region/<townvill>')
def get_region_timeline():
    """Get prediction timeline for a specific region"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    try:
        predictions = db.get_predictions_by_region(townvill, start_date, end_date)
        
        timeline_data = []
        for row in predictions:
            date, predicted_value, predicted_percentage = row
            timeline_data.append({
                "date": date,
                "predicted_value": predicted_value,
                "predicted_percentage": predicted_percentage
            })
        
        return jsonify({
            "townvill": townvill,
            "timeline": timeline_data
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/high-risk')
def get_high_risk_regions():
    """Get high-risk regions for a specific date"""
    selected_date = request.args.get('date')
    threshold = float(request.args.get('threshold', 50))
    
    if not selected_date:
        return jsonify({"error": "Missing date parameter"}), 400
    
    try:
        high_risk = db.get_high_risk_regions(selected_date, threshold)
        
        features = []
        for row in high_risk:
            townvill, town, predicted_percentage, geometry_json = row
            
            feature = {
                "type": "Feature",
                "properties": {
                    "townvill": townvill,
                    "town": town,
                    "predicted_case_lag_future_14_percentage": predicted_percentage,
                    "risk_level": "high"
                },
                "geometry": json.loads(geometry_json)
            }
            features.append(feature)
        
        geojson = {
            "type": "FeatureCollection",
            "features": features
        }
        
        return jsonify(geojson)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/summary/<date>')
def get_daily_summary(date):
    """Get daily summary statistics"""
    try:
        summary = db.get_daily_summary(date)
        
        if not summary:
            return jsonify({"error": "No summary data found for the specified date"}), 404
        
        summary_data = {
            "date": summary[0],
            "total_regions": summary[1],
            "total_predicted_cases": summary[2],
            "avg_prediction": summary[3],
            "max_prediction": summary[4],
            "min_prediction": summary[5],
            "high_risk_regions": summary[6],
            "medium_risk_regions": summary[7],
            "low_risk_regions": summary[8]
        }
        
        return jsonify(summary_data)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/stats')
def get_database_stats():
    """Get overall database statistics"""
    try:
        stats = db.get_database_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
