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
    'BND': '../mavis datasets/bnd.csv',
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
    
    # Read the CSV, skip the first 3 rows which contain headers and ticker info
    try:
        df = pd.read_csv(csv_filename, skiprows=3, header=None)
        
        # Rename columns
        df.columns = ['Date', 'Close', 'High', 'Low', 'Open', 'Volume'] if len(df.columns) >= 6 else ['Date', 'Close', 'High', 'Low', 'Open']
        
    except Exception as e:
        # Fallback: try reading without skiprows
        try:
            df = pd.read_csv(csv_filename)
            
            # Try to map common column names
            rename_map = {}
            for col in df.columns:
                col_lower = col.lower()
                if 'date' in col_lower:
                    rename_map[col] = 'Date'
                elif 'close' in col_lower or 'adj' in col_lower:
                    rename_map[col] = 'Close'
                elif 'high' in col_lower:
                    rename_map[col] = 'High'
                elif 'low' in col_lower:
                    rename_map[col] = 'Low'
                elif 'open' in col_lower:
                    rename_map[col] = 'Open'
                elif 'volume' in col_lower:
                    rename_map[col] = 'Volume'
            
            # Apply rename if mappings were found
            if rename_map:
                df = df.rename(columns=rename_map)
                
            # Ensure we have the required columns
            required_cols = ['Date', 'Close', 'High', 'Low', 'Open']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                raise ValueError(f"Required columns missing: {missing_cols}")
                
        except Exception as e2:
            # If all attempts fail, raise original error
            raise ValueError(f"Could not read CSV file: {str(e)}")
    
    # Convert Date to datetime
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Set Date as index
    df.set_index('Date', inplace=True)
    
    # Sort by date ascending
    df.sort_index(inplace=True)
    
    return df

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
            
        # Validate date parameters - use exactly what's provided by the frontend
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
            
        # Get stock data
        try:
            df = load_stock_data_from_csv(ticker)
        except ValueError as ve:
            return jsonify({"error": str(ve)}), 400
        except FileNotFoundError as fe:
            return jsonify({"error": str(fe)}), 404
        except Exception as e:
            return jsonify({"error": f"Error loading data for {ticker}: {str(e)}"}), 500
            
        # Filter data by date range
        df = df.loc[start_date_dt:end_date_dt]
        
        if df.empty:
            return jsonify({"error": f"No data available for {ticker} in the specified date range"}), 404
            
        # Prepare data for candlestick chart
        candlestick_data = []
        
        for date, row in df.iterrows():
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

def load_open_price_from_csv(ticker):
    """
    Load price data from CSV files
    """
    # Use the main data loading function
    df = load_stock_data_from_csv(ticker)
    return df['Open']

def load_close_price_from_csv(ticker):
    """
    Load price data from CSV files
    """
    # Use the main data loading function
    df = load_stock_data_from_csv(ticker)
    return df['Close']

def load_high_price_from_csv(ticker):
    """
    Load price data from CSV files
    """
    # Use the main data loading function
    df = load_stock_data_from_csv(ticker)
    return df['High']

def load_low_price_from_csv(ticker):
    """
    Load price data from CSV files
    """
    # Use the main data loading function
    df = load_stock_data_from_csv(ticker)
    return df['Low']

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
        supported_tickers = list(ETF_FILE_MAP.keys())
    
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
                # Use the full stock data function but we'll only use Close prices
                ticker_data = load_stock_data_from_csv(ticker)['Close']
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
        price_df = pd.DataFrame(all_data)
        
        # Calculate weighted portfolio value
        portfolio_df = pd.DataFrame(index=price_df.index)
        
        # Normalize each security to start at 1.0
        for ticker, weight in tickers_dict.items():
            normalized_prices = price_df[ticker] / price_df[ticker].iloc[0]
            portfolio_df[ticker] = normalized_prices * weight
        
        # Sum across all weighted components to get portfolio value
        portfolio_df['portfolio_value'] = portfolio_df.sum(axis=1)
        
        # Add date as a column (formatted as string)
        portfolio_df['date'] = portfolio_df.index.strftime('%Y-%m-%d')
        
        # Prepare final result
        result = {
            "portfolio_data": portfolio_df.reset_index()[['date', 'portfolio_value']].to_dict(orient='records'),
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