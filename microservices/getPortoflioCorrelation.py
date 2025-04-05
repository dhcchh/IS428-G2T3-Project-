from flask import Flask, request, jsonify
import pandas as pd
import numpy as np
from datetime import datetime
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes


@app.route('/api/get-close-price', methods=['POST'])
def get_close_prices():
    try:
        # Get date range from request
        data = request.get_json()
        start_date = pd.to_datetime(data.get('start_date'))
        end_date = pd.to_datetime(data.get('end_date'))
        etfs = data.get('tickers')

        if not start_date or not end_date:
            return jsonify({'error': 'Missing date parameters'}), 400

        # Define ETFs to process
        etf_prices = {}

        # Get close prices for each ETF
        for etf in etfs:
            try:
                # Get close prices using existing function
                prices = load_price_data_from_csv(etf)
                
                # # Filter by date range
                # mask = (prices.index >= start_date) & (prices.index <= end_date)
                # filtered_prices = prices[mask]
                
                # # Convert to list for JSON serialization
                # etf_prices[etf] = filtered_prices.tolist()

                etf_prices[etf] = prices.tolist()
                
            except Exception as e:
                return jsonify({'error': f'Error processing {etf}: {str(e)}'}), 500

        return jsonify({
            'prices': etf_prices,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d')
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


def load_price_data_from_csv(ticker):
    """
    Load price data from CSV files
    """
    # Map ticker symbols to their corresponding CSV filenames
    ticker_file_map = {
        'SPY': '../final datasets/spy data.csv',
        'GBTC': '../final datasets/gbtc data.csv',
        'VUG': '../final datasets/vug data.csv',
        'BRK-B': '../final datasets/brk-b data.csv',
        'SPLV': '../mavis datasets/splv.csv',
        'USMV': '../mavis datasets/usmv.csv',
        'BND': '../mavis datasets/bnd.csv',
        'AGG': '../mavis datasets/agg.csv',
        'UPRO': '../angela_datasets/upro.csv',
        'ARKK': '../angela_datasets/arkk.csv',
        'IWF': '../angela_datasets/IWF.csv',
        'QQQ': '../angela_datasets/qqq.csv',
    }

    # Check if ticker is supported
    if ticker not in ticker_file_map:
        raise ValueError(f"Data for {ticker} not available. Supported tickers: {', '.join(ticker_file_map.keys())}")
    
    csv_filename = ticker_file_map[ticker]
    
    if not os.path.exists(csv_filename):
        raise FileNotFoundError(f"CSV file not found: {csv_filename}")
    

    # 1. Check the format of the file - and load the data correctly
    df_preview = pd.read_csv(csv_filename, nrows=5)  
    num_columns = df_preview.shape[1]

    if num_columns == 6:  # 6-column datasets (XY, Angela Dataset)
        df = pd.read_csv(csv_filename, skiprows=3, header=None)
        df.columns = ['Date', 'Close', 'High', 'Low', 'Open', 'Volume'] 
        

    elif num_columns == 9:  # 9-column dataset (Mavis Dataset)
        df = pd.read_csv(csv_filename)
        df = df[['Date', 'Close', 'High', 'Low', 'Open', 'Volume']]  # Drop 'Adj Close', 'Dividends', 'Stock Splits'
    else:
        raise ValueError(f"Unexpected column format in {ticker}: {num_columns} columns detected.")

    
    # Convert Date to datetime
    if not pd.api.types.is_datetime64_any_dtype(df['Date']):
        try:
            # Try DD/MM/YY format first (for qqq, iwf, upro)
            df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%y')
        except ValueError:
            try:
                # Try YYYY-MM-DD format (for arkk)
                df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d')
            except ValueError:
                # If both fail, let pandas infer the format
                df['Date'] = pd.to_datetime(df['Date'])


    # Set Date as index
    df.set_index('Date', inplace=True)
    
    # Sort by date ascending
    df.sort_index(inplace=True)
    
    # Return only the Close price series
    return df['Close']





# # Uncomment this to Test the function
# support_tickers = ['SPY', 'GBTC', 'VUG', 'BRK-B', 'SPLV', 'USMV', 'BND', 'AGG', 'UPRO', 'ARKK', 'IWF', 'QQQ']

# try:
#     for ticker in support_tickers:
#         print(f"Processing ticker: {ticker}")
#         try:
#             # Call your existing function to load data for each ticker
#             tickers_df = load_price_data_from_csv(ticker)  # Passing the ticker for each iteration
#             print(f"Data for {ticker}:")
#             print(tickers_df)
        
#         except Exception as e:
#             print(f"Error processing {ticker}: {e}")

# except Exception as e:
#     print(f"Error: {e}")




if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5009)