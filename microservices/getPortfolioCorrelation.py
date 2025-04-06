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
        etfs = data.get('tickers', ['ARKK', 'IWF', 'QQQ', 'UPRO'])

        if not start_date or not end_date:
            return jsonify({'error': 'Missing date parameters'}), 400

        # Create response structure
        etf_prices = {}
        etf_data_frames = {}

        # Process each ETF
        for ticker in etfs:
            try:
                # Load price data from CSV
                price_series = load_price_data_from_csv(ticker)
                etf_data_frames[ticker] = price_series
                
                # Filter by date range
                mask = (price_series.index >= start_date) & (price_series.index <= end_date)
                filtered_prices = price_series[mask]
                
                if filtered_prices.empty:
                    print(f"No data found for {ticker} in the selected date range")
                    continue
                
                # Format for response
                etf_prices[ticker] = {
                    'dates': filtered_prices.index.strftime('%Y-%m-%d').tolist(),
                    'prices': filtered_prices.values.tolist()
                }
                
            except Exception as e:
                print(f"Error processing {ticker}: {str(e)}")
                # Continue with other ETFs even if one fails
                continue

        # Calculate correlation matrix
        correlation_matrix = calculate_correlation_matrix(etf_data_frames, etfs, start_date, end_date)

        return jsonify({
            'prices': etf_prices,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'correlation_matrix': correlation_matrix
        })

    except Exception as e:
        print(f"API Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

def calculate_correlation_matrix(etf_data_frames, etfs, start_date, end_date):
    """Calculate correlation matrix for the given ETFs and date range"""
    
    # Create a dictionary to store resampled price series
    filtered_series = {}
    
    # Log details about input data
    print("Input ETF Data Frames:")
    for ticker, series in etf_data_frames.items():
        print(f"{ticker}:")
        print(f"  Series length: {len(series)}")
        print(f"  Date range: {series.index.min()} to {series.index.max()}")
    
    # Filter each series by date range and resample to ensure alignment
    for ticker, series in etf_data_frames.items():
        if series is not None:
            # Filter by date range
            mask = (series.index >= start_date) & (series.index <= end_date)
            filtered = series[mask]
            if not filtered.empty:
                filtered_series[ticker] = filtered
    
    print("Filtered Series:")
    for ticker, series in filtered_series.items():
        print(f"{ticker}:")
        print(f"  Filtered length: {len(series)}")
        print(f"  Filtered date range: {series.index.min()} to {series.index.max()}")
    
    # If we have price data for at least 2 ETFs, calculate correlation
    if len(filtered_series) >= 2:
        # Create a DataFrame with all ETFs' price series
        df = pd.DataFrame(filtered_series)
        
        # Calculate correlation matrix
        corr_df = df.corr(method='pearson')
        
        print("Correlation Matrix:")
        print(corr_df)
        
        # Convert to the expected format for the frontend
        matrix = []
        
        for source in etfs:
            if source not in corr_df.columns:
                # If ETF is not in correlation matrix, add a row of zeros
                row = []
                for target in etfs:
                    correlation = 1.0 if source == target else 0.0
                    row.append({
                        'source': source,
                        'target': target,
                        'correlation': correlation
                    })
                matrix.append(row)
            else:
                # Add correlation values for this ETF
                row = []
                for target in etfs:
                    if target not in corr_df.index:
                        correlation = 1.0 if source == target else 0.0
                    else:
                        correlation = corr_df.loc[source, target]
                        # Handle NaN values
                        if pd.isna(correlation):
                            correlation = 0.0
                    
                    row.append({
                        'source': source,
                        'target': target,
                        'correlation': correlation
                    })
                matrix.append(row)
        
        return matrix
    else:
        # Create a matrix of zeros with 1.0 on diagonal
        matrix = []
        for source in etfs:
            row = []
            for target in etfs:
                correlation = 1.0 if source == target else 0.0
                row.append({
                    'source': source,
                    'target': target,
                    'correlation': correlation
                })
            matrix.append(row)
        
        return matrix

def load_price_data_from_csv(ticker):
    """
    Load price data from CSV files with flexible parsing for different header formats and date formats.
    """
    # Map ticker symbols to their corresponding CSV filenames
    ticker_file_map = {
        'UPRO': '../angela_datasets/upro.csv',
        'ARKK': '../angela_datasets/arkk.csv',
        'IWF': '../angela_datasets/iwf.csv',
        'QQQ': '../angela_datasets/qqq.csv',
        'USMV': '../mavis datasets/usmv.csv',
        'VYM': '../mavis datasets/vym.csv',
        'SPLV': '../mavis datasets/splv.csv',
        'AGG': '../mavis datasets/agg.csv'
    }

    # Check if ticker is supported
    if ticker not in ticker_file_map:
        raise ValueError(f"Data for {ticker} not available")

    csv_filename = ticker_file_map[ticker]

    if not os.path.exists(csv_filename):
        raise FileNotFoundError(f"CSV file not found: {csv_filename}")
    
    try:
        # Read the first few lines of the CSV file to determine its structure
        with open(csv_filename, 'r') as file:
            first_lines = [file.readline() for _ in range(4)]  # Read the first 4 lines
        
        # Check if the second row contains "Ticker", indicating type1 format
        if 'Ticker' in first_lines[1]:
            # This file has a custom header, skip the first 4 rows
            print(f"Custom header detected in {ticker}, skipping first 4 rows.")
            df = pd.read_csv(csv_filename, skiprows=4, header=None)
            # Manually assign column names for type1 format
            df.columns = ['Date', 'Close', 'High', 'Low', 'Open', 'Volume']
        else:
            # The file has a standard header (like the second example)
            print(f"Standard header detected in {ticker}.")
            df = pd.read_csv(csv_filename)
        
        # Now, parse the Date and Close columns in the usual way
        # Convert date column to datetime with infer_datetime_format=True for automatic format detection
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce', infer_datetime_format=True)

        # Clean up data: drop rows with invalid dates or missing 'Close' values
        df = df.dropna(subset=['Date'])
        df['Close'] = pd.to_numeric(df['Close'], errors='coerce')
        df = df.dropna(subset=['Close'])

        # Sort and set the Date column as the index
        df = df.sort_values('Date')
        df.set_index('Date', inplace=True)

        return df['Close']
        
    except Exception as e:
        print(f"Detailed error loading {ticker} data: {str(e)}")
        
        # More detailed error logging
        if 'df' in locals():
            print(f"DataFrame columns: {df.columns}")
            print(f"First few rows:\n{df.head()}")
        
        raise

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5009)