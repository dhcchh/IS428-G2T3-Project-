from flask import Flask, request, jsonify
import pandas as pd
import numpy as np
from datetime import datetime
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Map of ETF ticker symbols to their CSV file paths
ETF_FILE_MAP = {
    'SPLV': '../mavis datasets/splv.csv',
    'USMV': '../mavis datasets/usmv.csv',
    'VYM': '../mavis datasets/vym.csv',
    'AGG': '../mavis datasets/agg.csv',
    'UPRO': '../angela_datasets/upro.csv',
    'ARKK': '../angela_datasets/arkk.csv',
    'IWF': '../angela_datasets/iwf.csv',
    'QQQ': '../angela_datasets/qqq.csv'
}

def load_stock_data_from_csv(ticker):
    """
    Load full stock data from CSV files including OHLC data
    
    Parameters:
    ticker (str): The ticker symbol of the stock/ETF
    
    Returns:
    pandas.DataFrame: DataFrame with OHLC data
    """
    if ticker not in ETF_FILE_MAP:
        raise ValueError(f"Data for {ticker} not available. Supported tickers: {', '.join(ETF_FILE_MAP.keys())}")
    
    csv_filename = ETF_FILE_MAP[ticker]
    
    if not os.path.exists(csv_filename):
        raise FileNotFoundError(f"CSV file not found: {csv_filename}")
    
    # Try reading the CSV file - based on your CSV structure
    try:
        # First attempt: Try reading with standard headers
        # Your CSV format is Date, Open, High, Low, Close, Adj Close, Volume, Dividends, Stock Splits
        print(f"Attempting to read {csv_filename}")
        df = pd.read_csv(csv_filename)
        
        # Print the first few rows and columns to debug
        print(f"CSV columns: {list(df.columns)}")
        print(f"First 2 rows: {df.head(2)}")
        
        # Ensure we have the required columns and rename if needed
        required_cols = ['Date', 'Open', 'High', 'Low', 'Close']
        
        # Create a mapping for column renaming if needed
        rename_map = {}
        for col in df.columns:
            col_lower = col.lower()
            if 'date' in col_lower:
                rename_map[col] = 'Date'
            elif 'open' in col_lower:
                rename_map[col] = 'Open'
            elif 'high' in col_lower:
                rename_map[col] = 'High'
            elif 'low' in col_lower:
                rename_map[col] = 'Low'
            elif 'close' in col_lower and 'adj' not in col_lower:
                rename_map[col] = 'Close'
            elif 'adj' in col_lower and 'close' in col_lower:
                rename_map[col] = 'Adj Close'
            elif 'volume' in col_lower:
                rename_map[col] = 'Volume'
        
        # Apply rename if needed
        if rename_map:
            df = df.rename(columns=rename_map)
        
        # Verify we have all required columns
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Required columns missing after renaming: {missing_cols}")
            
    except Exception as e:
        print(f"Error reading CSV file {csv_filename}: {str(e)}")
        raise ValueError(f"Could not read CSV file: {str(e)}")
    
    # Convert Date to datetime and set as index
    try:
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)
        df.sort_index(inplace=True)
        
        # Check if we have data after processing
        if df.empty:
            print(f"Warning: Dataframe is empty after processing for {ticker}")
        
        return df
        
    except Exception as e:
        print(f"Error processing dates in {csv_filename}: {str(e)}")
        raise ValueError(f"Error processing dates: {str(e)}")

@app.route('/candlestick-data', methods=['POST'])
def get_candlestick_data():
    """
    Endpoint to retrieve OHLC (Open, High, Low, Close) data for candlestick charts
    
    Request JSON format:
    {
        "ticker": "ARKK",
        "start_date": "2020-01-01",
        "end_date": "2022-01-01"
    }
    
    For portfolio requests:
    {
        "ticker": "portfolio",
        "tickers": {
            "USMV": 0.25,
            "VYM": 0.25,
            "SPLV": 0.25,
            "AGG": 0.25
        },
        "initial_investment": 10000,
        "start_date": "2020-01-01",
        "end_date": "2022-01-01"
    }
    """
    try:
        # Get JSON data from request
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Missing request body"}), 400
            
        # Extract parameters
        ticker = data.get('ticker')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        # Validate ticker parameter
        if not ticker:
            return jsonify({"error": "Missing 'ticker' in request body"}), 400
            
        # Validate date parameters
        if not start_date or not end_date:
            return jsonify({"error": "Missing 'start_date' or 'end_date' in request body"}), 400
            
        try:
            # Convert string dates to datetime for filtering
            start_date_dt = pd.to_datetime(start_date)
            end_date_dt = pd.to_datetime(end_date)
            
            # Add one day to end_date to include it in the range
            end_date_dt = end_date_dt + pd.Timedelta(days=1)
        except Exception as e:
            return jsonify({"error": f"Invalid date format: {str(e)}"}), 400
        
        # Handle portfolio requests
        if ticker.lower() == 'portfolio':
            # Check for portfolio parameters
            if 'tickers' not in data or not isinstance(data['tickers'], dict):
                return jsonify({"error": "Portfolio requests require 'tickers' dictionary"}), 400
                
            tickers_dict = data['tickers']
            initial_investment = data.get('initial_investment', 10000)
            
            # Validate tickers
            supported_tickers = list(ETF_FILE_MAP.keys())
            for t in tickers_dict.keys():
                if t not in supported_tickers:
                    return jsonify({"error": f"Ticker {t} is not supported. Supported tickers: {', '.join(supported_tickers)}"}), 400
            
            # Ensure weights sum to approximately 1
            weights_sum = sum(tickers_dict.values())
            if not np.isclose(weights_sum, 1.0, atol=1e-2):
                return jsonify({"error": f"Weights should sum to 1, got {weights_sum}"}), 400
            
            # Load data for all tickers
            all_data = {}
            for t in tickers_dict.keys():
                try:
                    # Load and filter by date
                    df = load_stock_data_from_csv(t)
                    filtered_df = df.loc[start_date_dt:end_date_dt]
                    
                    if filtered_df.empty:
                        return jsonify({"error": f"No data for {t} in the specified date range"}), 404
                    
                    all_data[t] = filtered_df['Close']
                except Exception as e:
                    return jsonify({"error": f"Error loading data for {t}: {str(e)}"}), 500
            
            # Create DataFrame with all ticker data
            price_df = pd.DataFrame(all_data)
            
            # Calculate shares based on initial investment
            first_day_prices = price_df.iloc[0]
            shares = {}
            
            for t, weight in tickers_dict.items():
                allocation = initial_investment * weight
                price = first_day_prices[t]
                shares[t] = allocation / price
            
            # Calculate portfolio value for each day
            portfolio_df = pd.DataFrame(index=price_df.index)
            
            for t in tickers_dict.keys():
                portfolio_df[t] = price_df[t] * shares[t]
            
            portfolio_df['portfolio_value'] = portfolio_df.sum(axis=1)
            
            # Create OHLC data for the portfolio
            ohlc_data = []
            previous_close = None
            
            for date, row in portfolio_df.iterrows():
                value = row['portfolio_value']
                
                # For the first day, open = close
                if previous_close is None:
                    open_value = value
                else:
                    open_value = previous_close
                
                # Add some variance to high and low
                high_value = max(open_value, value) * (1 + 0.005 + 0.005 * np.random.random())
                low_value = min(open_value, value) * (1 - 0.005 - 0.005 * np.random.random())
                
                ohlc_data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'open': float(open_value),
                    'high': float(high_value),
                    'low': float(low_value),
                    'close': float(value),
                    'volume': 0  # Not meaningful for portfolio
                })
                
                previous_close = value
            
            # Return portfolio data
            result = {
                "ticker": "portfolio",
                "start_date": start_date,
                "end_date": end_date,
                "initial_investment": initial_investment,
                "candlestick_data": ohlc_data
            }
            
            return jsonify(result)
            
        else:
            # Single ticker request - existing logic
            try:
                df = load_stock_data_from_csv(ticker)
            except ValueError as ve:
                return jsonify({"error": str(ve)}), 400
            except FileNotFoundError as fe:
                return jsonify({"error": str(fe)}), 404
            except Exception as e:
                return jsonify({"error": f"Error loading data for {ticker}: {str(e)}"}), 500
                
            # Filter data by date range
            print(f"Filtering data for {ticker} from {start_date_dt} to {end_date_dt}")
            try:
                # Ensure we have data before filtering
                if df.empty:
                    return jsonify({"error": f"No data available for {ticker}"}), 404
                    
                # Filter by date
                filtered_df = df.loc[start_date_dt:end_date_dt]
                
                print(f"After filtering: {len(filtered_df)} rows remain")
                
                if filtered_df.empty:
                    return jsonify({"error": f"No data available for {ticker} in the specified date range"}), 404
                    
            except Exception as e:
                return jsonify({"error": f"Error filtering data: {str(e)}"}), 500
                
            # Prepare data for candlestick chart
            candlestick_data = []
            
            for date, row in filtered_df.iterrows():
                # Ensure all values are numeric
                try:
                    candlestick_data.append({
                        'date': date.strftime('%Y-%m-%d'),
                        'open': float(row['Open']),
                        'high': float(row['High']),
                        'low': float(row['Low']),
                        'close': float(row['Close']),
                        'volume': int(float(row['Volume'])) if 'Volume' in row and not pd.isna(row['Volume']) else 0
                    })
                except (ValueError, TypeError) as e:
                    print(f"Skipping data point for {date} due to invalid value: {e}")
                    continue
                
            # Return the result
            result = {
                "ticker": ticker,
                "start_date": start_date,
                "end_date": end_date,
                "candlestick_data": candlestick_data
            }
            
            return jsonify(result)
            
    except Exception as e:
        print(f"Error in candlestick-data endpoint: {str(e)}")
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

@app.route('/available-tickers', methods=['GET'])
def get_available_tickers():
    """
    Endpoint to retrieve the list of available tickers
    """
    available_tickers = list(ETF_FILE_MAP.keys())
    
    return jsonify({
        "available_tickers": available_tickers
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5007)