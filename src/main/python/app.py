from flask import Flask, render_template, jsonify, request
import geopandas as gpd
import pandas as pd
import os

app = Flask(__name__,
            static_folder=os.path.abspath('src/main/resources/assets'),
            template_folder=os.path.abspath('src/main/resources'))

# Get the absolute path to the project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
data_path = os.path.join(project_root, '20250804xgboost_future14_case_results.geojson')

# Load your data
gdf = gpd.read_file(data_path)
gdf['date'] = pd.to_datetime(gdf['date']).dt.strftime('%Y-%m-%d')
unique_dates = sorted(gdf['date'].unique().tolist())

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/dates')
def get_dates():
    return jsonify(unique_dates)

@app.route('/api/data')
def get_data_by_date():
    selected_date = request.args.get('date')
    if not selected_date or selected_date not in unique_dates:
        return jsonify({"error": "Invalid or missing date parameter"}), 400

    filtered_gdf = gdf[gdf['date'] == selected_date]
    
    # Convert to a format that can be JSON serialized (like GeoJSON)
    return jsonify(filtered_gdf.to_geo_json())

if __name__ == '__main__':
    app.run(debug=True)
