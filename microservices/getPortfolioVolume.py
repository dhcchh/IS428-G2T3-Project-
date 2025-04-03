from flask import Flask, request, jsonify
import pandas as pd
import numpy as np
from datetime import datetime
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

def load_volume_data_from_csv(ticker):
    """
    Load price data from CSV files
    """
    # Map ticker symbols to their corresponding CSV filenames
    ticker_file_map = {
        'SPY': '../xy datasets/spy data.csv',
        'GBTC': '../xy datasets/gbtc data.csv',
        'VUG': '../xy datasets/vug data.csv',
        'BRK-B': '../xy datasets/brk-b data.csv',
        'SPLV': '../mavis datasets/splv.csv',
        'USMV': '../mavis datasets/usmv.csv',
        'BND': '../mavis datasets/bnd.csv',
        'AGG': '../mavis datasets/agg.csv',
        'UPRO': '../angela_datasets/upro.csv',
        'ARKK': '../angela_datasets/arkk.csv',
        'IWF': '../angela_datasets/IWF.csv',
        'QQQ': '../angela_datasets/qqq.csv'

    }
    
    # Check if ticker is supported
    if ticker not in ticker_file_map:
        raise ValueError(f"Data for {ticker} not available. Supported tickers: {', '.join(ticker_file_map.keys())}")
    
    csv_filename = ticker_file_map[ticker]
    
    if not os.path.exists(csv_filename):
        raise FileNotFoundError(f"CSV file not found: {csv_filename}")
    
    # Read CSV without skipping rows initially to detect format
    df_preview = pd.read_csv(csv_filename, nrows=5)  # Read first 5 rows to inspect structure
    num_columns = df_preview.shape[1]


    # IMPORTANT: Determine whether to skip rows based on column count
    if num_columns == 6:  # 6-column datasets (XY, Angela Dataset)
        df = pd.read_csv(csv_filename, skiprows=3, header=None)
        df.columns = ['Date', 'Close', 'High', 'Low', 'Open', 'Volume'] 

    elif num_columns == 9:  # 9-column dataset (Mavis Dataset)
        df = pd.read_csv(csv_filename)
        df = df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]  # Drop 'Adj Close', 'Dividends', 'Stock Splits'
    else:
        raise ValueError(f"Unexpected column format in {ticker}: {num_columns} columns detected.")


    # Convert Date to datetime
    df['Date'] = pd.to_datetime(df['Date'])    
    
    # Set Date as index
    df.set_index('Date', inplace=True)
    
    # Sort by date ascending
    df.sort_index(inplace=True)
    
    # Return only the Close price series
    return df['Volume']


@app.route('/portfolio-data', methods=['POST'])
def get_portfolio_price_data():
    """
    Endpoint to retrieve historical price data for a portfolio of ETFs
    
    Request JSON format:
    {
        "tickers": {
            "SPY": 1.0  # Currently only SPY is supported
        }
    }
    
    Where the keys are ticker symbols and values are the weightages (should sum to 1)
    """
    try:
        # Get JSON data from request
        data = request.get_json()
        
        if not data or 'tickers' not in data:
            return jsonify({"error": "Missing 'tickers' in request body"}), 400
        
        tickers_dict = data['tickers']
        
        # Validate the input
        if not tickers_dict or not isinstance(tickers_dict, dict):
            return jsonify({"error": "Tickers should be a non-empty dictionary"}), 400
        
        # Check if all requested tickers are supported
        supported_tickers = ['SPY', 'GBTC', 'VUG', 'BRK-B', 'SPLV', 'USMV', 'BND', 'AGG', 'UPRO', 'ARKK', 'IWF', 'QQQ']
        for ticker in tickers_dict.keys():
            if ticker not in supported_tickers:
                return jsonify({"error": f"Ticker {ticker} is not supported. Supported tickers: {', '.join(supported_tickers)}"}), 400
        
        # Ensure weights sum to approximately 1 (allowing for float precision)
        weights_sum = sum(tickers_dict.values())
        if not np.isclose(weights_sum, 1.0, atol=1e-2):
            return jsonify({"error": f"Weights should sum to 1, got {weights_sum}"}), 400
        
        # Download data for all tickers
        all_data = {}
        for ticker in tickers_dict.keys():
            try:
                ticker_data = load_volume_data_from_csv(ticker)
                if ticker_data.empty:
                    return jsonify({"error": f"No data found for ticker: {ticker}"}), 404
                all_data[ticker] = ticker_data
            except ValueError as ve:
                return jsonify({"error": str(ve)}), 400
            except FileNotFoundError as fe:
                return jsonify({"error": str(fe)}), 404
            except Exception as e:
                return jsonify({"error": f"Error fetching data for {ticker}: {str(e)}"}), 500
        
        # Combine all price data
        vol_df = pd.DataFrame(all_data)
        
        # Calculate weighted portfolio value
        portfolio_df = pd.DataFrame(index=vol_df.index)
        
        # Apply the weight to the volume (no normalization)
        for ticker, weight in tickers_dict.items():
            portfolio_df[ticker] = vol_df[ticker] * weight
        
        # Sum across all weighted components to get portfolio volume
        portfolio_df['portfolio_volume'] = portfolio_df.sum(axis=1)
        
        # Add date as a column (formatted as string)
        portfolio_df['date'] = portfolio_df.index.strftime('%Y-%m-%d')
        
        # Prepare final result
        ## convert data into a dict {date: portfolio volume}
        result = {
            "portfolio_data": portfolio_df.reset_index()[['date', 'portfolio_volume']].to_dict(orient='records'),
            "component_data": {}
        }
        
        # Add individual component data
        for ticker in tickers_dict.keys():
            component_df = pd.DataFrame({
                'date': price_df.index.strftime('%Y-%m-%d'),
                'price': price_df[ticker],
                'normalized_price': price_df[ticker] / price_df[ticker].iloc[0]
            })
            result["component_data"][ticker] = component_df.to_dict(orient='records')
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

@app.route('/available-etfs', methods=['GET'])
def get_available_etfs():
    """
    Return a list of available ETFs that can be used in the portfolio
    """
    available_etfs = {
        "SPY": "SPDR S&P 500 ETF Trust",
        "GBTC": "Grayscale Bitcoin Trust",
        "VUG": "Vanguard Growth ETF",
        "BRK-B": "Berkshire Hathaway Inc. Class B"
    }
    
    return jsonify(available_etfs)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5003)