from flask import Flask, request, jsonify
import pandas as pd
import numpy as np
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

def safe_float(value, default=0.0):
    """
    Safely convert value to float, handling various input types
    """
    try:
        # Handle string representations of numbers
        if isinstance(value, str):
            # Remove any percentage signs, commas, and whitespace
            value = value.replace('%', '').replace(',', '').strip()
        
        # Convert to float
        converted = float(value)
        
        # Handle percentage representation: If the value is above 1, it's assumed to be a percentage (e.g., 25 instead of 0.25)
        if converted > 1 and converted <= 100:
            converted /= 100  # Convert to a decimal (e.g., 25 -> 0.25)
        elif converted > 100:
            # If it's larger than 100 (like 12362%), assume it's a wrongly parsed value and divide by 100
            converted /= 100
        
        return converted
    except (ValueError, TypeError):
        return default

def load_company_allocation_data(ticker):
    """
    Load company allocation data from CSV files and calculate industry weights
    """
    # Mapping of tickers to their allocation CSV files
    ticker_file_map = {
        'SPY': '../final datasets/spy_share_allocation.csv',
        'GBTC': '../final datasets/gbtc_share_allocation.csv',
        'VUG': '../final datasets/vug_share_allocation.csv',
        'BRK-B': '../final datasets/BRK-B_share_allocation.csv',
        'UPRO': '../angela_datasets/upro_share_allocation.csv',
        'QQQ': '../angela_datasets/qqq_share_allocation.csv',
        'IWF': '../angela_datasets/IWF_share_allocation.csv',
        'ARKK': '../angela_datasets/arkk_share_allocation.csv',
        'USMV': '../mavis datasets/usmv_share_allocation.csv',
        'VYM': '../mavis datasets/vym_share_allocation.csv',
        'SPLV': '../mavis datasets/splv_share_allocation.csv',
        'AGG': '../mavis datasets/agg_share_allocation.csv'
    }
    
    # Validate ticker
    if ticker not in ticker_file_map:
        raise ValueError(f"Company allocation for {ticker} not supported")
    
    # Get file path
    csv_filename = ticker_file_map[ticker]
    
    # Check if file exists
    if not os.path.exists(csv_filename):
        raise FileNotFoundError(f"CSV file not found: {csv_filename}")
    
    # Read CSV
    try:
        df = pd.read_csv(csv_filename)
    except Exception as e:
        raise ValueError(f"Error reading CSV file {csv_filename}: {str(e)}")
    
    # Define possible column names
    name_columns = ['Name', 'Company', 'Holdings', 'Security']
    weight_columns = ['Weight', 'Percent', 'Percent_of_Fund', '%', 'Market Value']
    industry_columns = ['Industry']
    
    # Identify columns
    name_col = next((col for col in name_columns if col in df.columns), None)
    weight_col = next((col for col in weight_columns if col in df.columns), None)
    industry_col = next((col for col in industry_columns if col in df.columns), None)
    
    if not name_col:
        raise ValueError(f"No company name column found in {csv_filename}")
    
    if not weight_col:
        # Try to infer weight from other columns
        if 'Shares Held' in df.columns and 'Market Value' in df.columns:
            df[weight_col] = df['Market Value']
        else:
            raise ValueError(f"No weight column found in {csv_filename}")
    
    if not industry_col:
        raise ValueError(f"No industry column found in {csv_filename}")
    
    # Clean and prepare data
    df = df[df[name_col].notna() & (df[name_col] != '--')]
    
    # Convert weights to numeric, handling potential string representations
    df[weight_col] = df[weight_col].apply(safe_float)
    
    # Group by Industry and sum the weights for each industry
    industry_weightage = df.groupby(industry_col)[weight_col].sum().reset_index()
    
    # Normalize the weights to ensure the total weight sums to 100
    industry_weightage['Weight'] = industry_weightage[weight_col] / industry_weightage[weight_col].sum() * 100
    
    # Sort and limit to top 10 industries
    industry_weightage = industry_weightage.sort_values('Weight', ascending=False)
    industry_weightage = industry_weightage.head(10)
    
    return industry_weightage

@app.route('/portfolio-industry-weightage', methods=['POST'])
def get_portfolio_industry_weightage():
    """
    Endpoint to retrieve combined industry allocation for multiple ETFs
    """
    try:
        # Get JSON data from request
        data = request.get_json()
        
        # Validate input
        if not data or 'tickers' not in data:
            return jsonify({"error": "Missing 'tickers' in request body"}), 400
        
        tickers_dict = data['tickers']
        
        if not isinstance(tickers_dict, dict) or not tickers_dict:
            return jsonify({"error": "Tickers should be a non-empty dictionary"}), 400
        
        # Combine industry allocations
        combined_industries = {}
        
        for ticker, etf_weight in tickers_dict.items():
            try:
                # Ensure etf_weight is converted to a float
                etf_weight = safe_float(etf_weight, default=0.25)
                
                # Load industry allocation for this ticker
                ticker_data = load_company_allocation_data(ticker)
                
                # Combine with existing data
                for _, row in ticker_data.iterrows():
                    industry = row['Industry']
                    weight = row['Weight'] * etf_weight
                    
                    # Debugging: log each weight calculation to check if any weights are too large
                    print(f"Processing {industry}: row['Weight'] = {row['Weight']}, etf_weight = {etf_weight}, combined weight = {weight}")
                    
                    if industry in combined_industries:
                        combined_industries[industry] += weight
                    else:
                        combined_industries[industry] = weight
            
            except Exception as e:
                print(f"Error processing {ticker}: {str(e)}")
                continue
        
        # Convert to dataframe and sort
        result_df = pd.DataFrame.from_dict(combined_industries, orient='index', columns=['Weight'])
        result_df.index.name = 'Industry'
        result_df = result_df.reset_index()
        result_df = result_df.sort_values('Weight', ascending=False)
        
        # Limit to top industries, create 'Others' category
        top_industries = result_df.head(10)
        others_weight = result_df.iloc[10:]['Weight'].sum()
        
        if others_weight > 0:
            others_row = pd.DataFrame({
                'Industry': ['Others'],
                'Weight': [others_weight]
            })
            top_industries = pd.concat([top_industries, others_row], ignore_index=True)
        
        # Convert to list of dictionaries
        result = top_industries.to_dict(orient='records')
        
        return jsonify({
            "portfolio_industry_allocation": result
        })
    
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

@app.route('/available-etfs', methods=['GET'])
def get_available_etfs():
    """
    Return a list of available ETFs
    """
    available_etfs = {
        "SPY": "S&P 500 ETF",
        "GBTC": "Grayscale Bitcoin Trust",
        "VUG": "Vanguard Growth ETF",
        "BRK-B": "Berkshire Hathaway B",
        "UPRO": "ProShares UltraPro S&P500",
        "QQQ": "Invesco QQQ Trust",
        "IWF": "iShares Russell 1000 Growth",
        "ARKK": "ARK Innovation ETF",
        "USMV": "iShares MSCI USA Min Vol Factor",
        "VYM": "Vanguard High Dividend Yield",
        "SPLV": "Invesco S&P 500 Low Volatility",
        "AGG": "iShares Core US Aggregate Bond"
    }
    
    return jsonify(available_etfs)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5006)