# FRONTEND
## When html page loads, get the MIN & MAX Date of ETFs from the backend
## set selectedStartDate & selectedEndDate = Min & Max Date as default
## note: when user changes the time button (1mth, 6mth, 1yr), the selectedStartDate & selectedEndDate variable will be updated
## set initial allocations of each ETF to 0.25 (25% each) in the frontend
## note: when user changes the slider allocations of each ETF update the allocation

## Then, call the function calculate_and_fetch_results
## - sends selectedStartDate and selectedStartDate to backend
## - sends allocations to backend
## - sends initial investment to backend
## Retrieve the combined volume dataframe from the backend
## - then, plot the combined volume dataframe using d3 line chart

# BACKEND
## In this .py file
## 1. Function to Extract the Min & Max date from CSV files
## - Min & Max date are equal for all the 4 ETFs (arkk, qqq, iwf, upro)
## - hence retrieve Min & Max from qqq only
## - however, the date format may differ 22/3/24 (qqq, iwf, upro) or 2024-03-22 (arkk)

## 2. Function to Calculate result for the volume chart
## - based on start & end date, and allocation do the following:
## - a. Call my existing function to load the volume data for each ticker
## - b. Filter each ETF data based on start & end date 
##      - Note: the date format in the CSV files may be different from the selectedStartDate & selectedEndDate in the frontend (22/3/24 in csv vs 2024-03-22)
##      - If different, account for this and filter the csv files based on the selectedStartDate & selectedEndDate (current csv format is: 22/3/24 date for (qqq, iwf, upro) and 2024-03-22 date for(arkk))
## - c. Then, create a dataframe that contains the 1) Date column  2) combined ETFs volume column based on allocation (0.25, 0.25) 
##      - Combined volume = sum the volume of each adjusted ETF volume  (ETF1_volume*allocation  +  ETF2_volume*allocation + ETF3_volume*allocation + ETF4_volume*allocation)
## - d. Return the combined volume dataframe to the frontend

## For the function add checks at each step to ensure data is retrieved etc.


## 1. From frontend
## - send the start & end data, and allocation, and tickers. 



from flask import Flask, request, jsonify
import pandas as pd
import numpy as np
from datetime import datetime
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes



## 2. Receive data from FrontEnd
@app.route('/api/volume-analysis', methods=['POST'])
def get_volume():
    try:
        # Get date range from request
        data = request.get_json()
        start_date = pd.to_datetime(data.get('start_date'))
        end_date = pd.to_datetime(data.get('end_date'))
        allocations = data.get('allocations')
        etfs = data.get('tickers')

        if not start_date or not end_date:
            return jsonify({'error': 'Missing date parameters'}), 400

        # Create a volume dictionary
        etf_volume = {}
        for etf in etfs:
            try:
                volume = load_volume_data_from_csv(etf)
                
                # Filter by date range
                mask = (volume.index >= start_date) & (volume.index <= end_date)
                filtered_volume = volume[mask]

                # Create dictionary with dates and volumes
                etf_volume[etf] = {
                    'dates': filtered_volume.index.strftime('%Y-%m-%d').tolist(),
                    'volumes': filtered_volume.values.tolist()
                }
                
        
            except Exception as e:
                return jsonify({'error': f'Error processing {etf}: {str(e)}'}), 500

        
        
        return jsonify({
            'volume': etf_volume,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'allocations' : allocations
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# def get_volume1():
#     try:
#         # Get date range from request
#         data = request.get_json()
#         start_date = pd.to_datetime(data.get('start_date'))
#         end_date = pd.to_datetime(data.get('end_date'))
#         allocations = data.get('allocations')
#         etfs = data.get('tickers')

#         if not start_date or not end_date:
#             return jsonify({'error': 'Missing date parameters'}), 400
        

#         # Initialize empty DataFrame for combined data
#         etf_volume = {}
#         # combined_df = pd.DataFrame()
#         for etf in etfs:
#             try:
#                 volume = load_volume_data_from_csv(etf)
                
#                 # Filter by date range
#                 mask = (volume.index >= start_date) & (volume.index <= end_date)
#                 filtered_volume = volume[mask]


#                 # # Multiply volume by allocation (convert percentage to decimal)
#                 # allocation = allocations.get(etf, 0) / 100
#                 # weighted_volume = filtered_volume * allocation
                


#                 # Create dictionary with dates and volumes
#                 etf_volume[etf] = {
#                     'dates': filtered_volume.index.strftime('%Y-%m-%d').tolist(),
#                     'volumes': filtered_volume.values.tolist()
#                 }
                
#             except Exception as e:
#                 return jsonify({'error': f'Error processing {etf}: {str(e)}'}), 500

        
        
#         return jsonify({
#             'volume': etf_volume,
#             'start_date': start_date.strftime('%Y-%m-%d'),
#             'end_date': end_date.strftime('%Y-%m-%d'),
#             'allocations': allocations
#         })

#     except Exception as e:
#         return jsonify({'error': str(e)}), 500













def load_volume_data_from_csv(ticker):
    """
    Load price data from CSV files
    """
    # Map ticker symbols to their corresponding CSV filenames
    ticker_file_map = {
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
    

    # Read the CSV, skip the first 3 rows which contain headers and ticker info
    df = pd.read_csv(csv_filename, skiprows=3, header=None)
    df.columns = ['Date', 'Close', 'High', 'Low', 'Open', 'Volume'] 

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
    
    
    # Return only the Volume series
    return df['Volume']




### get min & max date from QQQ data (to standardize min & mad date for all ETFs
# @app.route('/api/get-date-range', methods=['GET'])
# def get_date_range():
#     """
#     Function to extract MIN & MAX dates from QQQ data
#     Returns min_date and max_date in YYYY-MM-DD format
#     """
#     try:
#         # Load QQQ data
#         qqq_volume = load_volume_data_from_csv('QQQ')
        
#         # Get min and max dates from index
#         min_date = qqq_volume.index.min()
#         max_date = qqq_volume.index.max()
         
#         # Convert dates to standard format (YYYY-MM-DD)
#         if isinstance(min_date, str):
#             min_date = pd.to_datetime(min_date, format='%d/%m/%y').strftime('%Y-%m-%d')
#             max_date = pd.to_datetime(max_date, format='%d/%m/%y').strftime('%Y-%m-%d')
#         else:
#             min_date = min_date.strftime('%Y-%m-%d')
#             max_date = max_date.strftime('%Y-%m-%d')
            
#         return {
#             'min_date': min_date,
#             'max_date': max_date
#         }
#     except Exception as e:
#         raise Exception(f"Error getting date range: {str(e)}")


def calculate_combined_volume(start_date, end_date, allocations):
    """
    Calculate combined volume based on date range and allocations
    Parameters:
        start_date (str): Start date in YYYY-MM-DD format
        end_date (str): End date in YYYY-MM-DD format
        allocations (dict): Dictionary with ETF allocations (e.g., {'ARKK': 0.25, 'QQQ': 0.25, ...})
    Returns:
        JSON with dates and combined volumes
    """
    try:
        # Convert selected dates to datetime
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
        
        # Initialize empty DataFrame for combined data
        combined_df = pd.DataFrame()
        
        # Load and process each ETF's data
        for etf, allocation in allocations.items():
            # Load volume data for this ETF
            volume_series = load_volume_data_from_csv(etf)
            
            # Convert index to datetime if it's string
            if isinstance(volume_series.index[0], str):
                volume_series.index = pd.to_datetime(volume_series.index, format='%d/%m/%y')
            
            # Filter by date range
            mask = (volume_series.index >= start_dt) & (volume_series.index <= end_dt)
            filtered_volume = volume_series[mask]
            
            # Multiply volume by allocation
            weighted_volume = filtered_volume * allocation
            
            # Add to combined DataFrame
            if combined_df.empty:
                combined_df['Volume'] = weighted_volume
            else:
                combined_df['Volume'] += weighted_volume
        
        # Convert dates to string format for JSON serialization
        result = {
            'dates': combined_df.index.strftime('%Y-%m-%d').tolist(),
            'volumes': combined_df['Volume'].tolist()
        }
        
        return jsonify(result)
    
    except Exception as e:
        raise Exception(f"Error calculating combined volume: {str(e)}")





if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5008)

    
