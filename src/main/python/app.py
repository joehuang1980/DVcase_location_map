from flask import Flask, render_template, jsonify
import pandas as pd
import os

app = Flask(__name__,
            static_folder=os.path.abspath('src/main/resources/assets'),
            template_folder=os.path.abspath('src/main/resources'))

# Load your data
df = pd.read_csv(os.path.join(os.path.dirname(__file__), '../../../../../20250804xgboost_future14_case_results.geojson'))
df['date'] = pd.to_datetime(df['date'])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data')
def get_data():
    # Convert dataframe to a list of dictionaries
    data = df.to_dict(orient='records')
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)
