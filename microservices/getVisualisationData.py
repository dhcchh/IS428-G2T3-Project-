from flask import Flask, request, jsonify
import pandas as pd
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "ok"})

@app.route('/api/real-vs-nominal', methods=['GET'])
def get_real_vs_nominal_data():
    """
    Endpoint to provide data for real vs nominal visualization
    Returns data from spy_inflation.csv with date, nominal_inv_10k, real_inv_10k
    """
    try:
        # Path to the data file
        file_path = 'spy_inflation.csv'
        
        # Check if file exists
        if not os.path.exists(file_path):
            return jsonify({"error": f"Data file not found: {file_path}"}), 404
        
        # Read the CSV file
        df = pd.read_csv(file_path)
        
        # Ensure required columns exist
        required_columns = ['date', 'nominal_inv_10k', 'real_inv_10k']
        for col in required_columns:
            if col not in df.columns:
                return jsonify({"error": f"Required column '{col}' not found in data file"}), 400
        
        # Select only the columns we need
        result_df = df[required_columns].copy()
        
        # Sample every 4th row to reduce data size
        sampled_df = result_df.iloc[::4, :]
        
        # Convert to list of dictionaries for JSON serialization
        result = sampled_df.to_dict(orient='records')
        
        return jsonify({
            "data": result,
            "status": "success"
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/bank-vs-spy', methods=['GET'])
def get_bank_vs_spy_data():
    """
    Endpoint to provide data for bank vs spy visualization
    Returns merged data from bank_values.csv and spy_inflation.csv with real values
    """
    try:
        # Paths to the data files
        bank_file_path = 'bank_values.csv'
        spy_file_path = 'spy_inflation.csv'
        
        # Check if files exist
        if not os.path.exists(bank_file_path):
            return jsonify({"error": f"Bank data file not found: {bank_file_path}"}), 404
        if not os.path.exists(spy_file_path):
            return jsonify({"error": f"SPY data file not found: {spy_file_path}"}), 404
        
        # Read the CSV files
        bank_df = pd.read_csv(bank_file_path)
        spy_df = pd.read_csv(spy_file_path)
        
        # Ensure required columns exist
        if 'date' not in bank_df.columns or 'real_value' not in bank_df.columns:
            return jsonify({"error": "Required columns not found in bank data file"}), 400
        if 'date' not in spy_df.columns or 'real_inv_10k' not in spy_df.columns:
            return jsonify({"error": "Required columns not found in SPY data file"}), 400
        
        # Merge the dataframes on date
        bank_data = bank_df[['date', 'real_value']].rename(columns={'real_value': 'bank_value'})
        spy_data = spy_df[['date', 'real_inv_10k']].rename(columns={'real_inv_10k': 'spy_value'})
        
        merged_df = pd.merge(bank_data, spy_data, on='date', how='inner')
        
        # Sample every 4th row to reduce data size
        sampled_df = merged_df.iloc[::4, :]
        
        # Convert to list of dictionaries for JSON serialization
        result = sampled_df.to_dict(orient='records')
        
        return jsonify({
            "data": result,
            "status": "success"
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/inflation-stats', methods=['GET'])
def get_inflation_stats():
    """
    Endpoint to provide inflation statistics for display
    """
    try:
        # These could be calculated from your data, but for now we'll use fixed values
        # based on your project proposal
        stats = {
            "singapore_inflation": 1.8,  # From your proposal: "Singapore's core inflation in December 2024 was 1.8%"
            "global_inflation": 4.5,     # From your proposal: "global headline inflation... to 4.5% in 2025"
            "bank_interest": 0.5,        # Typical savings account interest
            "spy_return_range": {
                "min": 7,
                "max": 10
            }
        }
        
        return jsonify({
            "data": stats,
            "status": "success"
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# If this file is run directly, start the Flask server
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5005))  # Use a different port from other microservices
    app.run(debug=True, host='0.0.0.0', port=port)