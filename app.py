from flask import Flask, render_template, jsonify
import pandas as pd

app = Flask(__name__)

# Load your data
df = pd.read_csv('/home/joe/Documents/2023_semi_supervised_learning/台南未來病例預測模型/xgboost/20250804xgboost_future14_case_results.csv')
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
