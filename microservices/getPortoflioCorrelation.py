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
    
    # Filter each series by date range and resample to ensure alignment
    for ticker, series in etf_data_frames.items():
        if series is not None:
            # Filter by date range
            mask = (series.index >= start_date) & (series.index <= end_date)
            filtered = series[mask]
            if not filtered.empty:
                filtered_series[ticker] = filtered
    
    # If we have price data for at least 2 ETFs, calculate correlation
    if len(filtered_series) >= 2:
        # Create a DataFrame with all ETFs' price series
        df = pd.DataFrame(filtered_series)
        
        # Calculate correlation matrix
        corr_df = df.corr(method='pearson')
        
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
    Load price data from CSV files
    """
    # Map ticker symbols to their corresponding CSV filenames
    ticker_file_map = {
        'UPRO': '../angela_datasets/upro.csv',
        'ARKK': '../angela_datasets/arkk.csv',
        'IWF': '../angela_datasets/iwf.csv',
        'QQQ': '../angela_datasets/qqq.csv',
    }

    # Check if ticker is supported
    if ticker not in ticker_file_map:
        raise ValueError(f"Data for {ticker} not available")
    
    csv_filename = ticker_file_map[ticker]
    
    # Verify file exists
    if not os.path.exists(csv_filename):
        print(f"File not found: {csv_filename}")
        # Try looking in the current directory
        alternative_path = f"{ticker.lower()}.csv"
        if os.path.exists(alternative_path):
            csv_filename = alternative_path
        else:
            raise FileNotFoundError(f"CSV file not found: {csv_filename}")
    
    # Try to load the CSV with appropriate settings
    try:
        # Skip rows to account for header format in the CSV
        df = pd.read_csv(csv_filename, skiprows=3, header=None)
        
        # Assign appropriate column names
        if len(df.columns) >= 6:
            df.columns = ['Date', 'Close', 'High', 'Low', 'Open', 'Volume']
        else:
            # Handle CSVs with fewer columns
            column_names = ['Date', 'Close']
            for i in range(2, len(df.columns)):
                column_names.append(f'Col{i+1}')
            df.columns = column_names
        
        # Better date parsing based on format detection
        if 'Date' in df.columns:
            # Check format of the first non-null value
            sample_dates = df['Date'].dropna().head(5).tolist()
            if sample_dates:
                sample_date = str(sample_dates[0])
                
                # Select appropriate format based on pattern
                if '-' in sample_date:  # Format like 2024-03-22
                    df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d', errors='coerce')
                elif '/' in sample_date:  # Format like 22/3/24
                    if len(sample_date) <= 8:  # Short format like 22/3/24
                        df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%y', errors='coerce')
                    else:  # Longer format like 22/03/2024
                        df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y', errors='coerce')
                else:
                    # Fallback to dateutil parser
                    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            else:
                # No valid sample date found, use default parser
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        else:
            raise ValueError(f"Date column not found in {ticker} data")
        
        # Drop rows with NaN dates
        df = df.dropna(subset=['Date'])
        
        # Ensure Close is numeric
        df['Close'] = pd.to_numeric(df['Close'], errors='coerce')
        
        # Drop rows with NaN Close values
        df = df.dropna(subset=['Close'])
        
        # Set Date as index
        df.set_index('Date', inplace=True)
        
        # Sort by date
        df = df.sort_index()
        
        # Return just the Close price series
        return df['Close']
        
    except Exception as e:
        print(f"Error loading {ticker} data: {str(e)}")
        raise

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5009)