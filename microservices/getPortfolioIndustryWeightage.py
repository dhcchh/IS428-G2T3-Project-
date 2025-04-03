from flask import Flask, request, jsonify
import pandas as pd
import numpy as np
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

def load_industry_allocation_data(ticker):
    """
    Load industry allocation data from CSV files
    """
    # Map ticker symbols to their corresponding allocation CSV filenames
    ticker_file_map = {
        'SPY': '../xy datasets/spy_share_allocation.csv',
        'GBTC': '../xy datasets/gbtc_share_allocation.csv',
        'VUG': '../xy datasets/vug_share_allocation.csv',
        'BRK-B': '../xy datasets/BRK-B_share_allocation.csv',
        'VYM': '../mavis datasets/vym_share_allocation.csv',
        'SPLV': '../mavis datasets/splv_share_allocation.csv',
        'USMV': '../mavis datasets/usmv_share_allocation.csv',
        'BND': '../mavis datasets/bnd_share_allocation.csv',
        'AGG': '../mavis datasets/agg_share_allocation.csv',
        'UPRO': '../angela_datasets/upro_share_allocation.csv',
        'ARKK': '../angela_datasets/arkk_share_allocation.csv',
        'IWF': '../angela_datasets/IWF_share_allocation.csv',
        'QQQ': '../angela_datasets/qqq_share_allocation.csv'
    }
    
    # Check if ticker is supported
    if ticker not in ticker_file_map:
        raise ValueError(f"Industry allocation for {ticker} not available. Supported tickers: {', '.join(ticker_file_map.keys())}")
    
    csv_filename = ticker_file_map[ticker]
    
    if not os.path.exists(csv_filename):
        raise FileNotFoundError(f"CSV file not found: {csv_filename}")
    
    # Read the CSV file
    df = pd.read_csv(csv_filename)
    
    # Check if industry/sector column exists (different files might have different column names)
    industry_column = None
    for col in ['Sector', 'Industry', 'Category']:
        if col in df.columns:
            industry_column = col
            break
    
    if not industry_column:
        raise ValueError(f"No industry/sector column found in {csv_filename}")
    
    # For BND and AGG (bond ETFs), use different processing
    if ticker in ['BND', 'AGG']:
        # Bonds typically use 'Category' or similar as their classification
        weight_column = None
        for col in ['Percent_of_Fund', 'Weight', 'Market_Value']:
            if col in df.columns:
                weight_column = col
                break
                
        if not weight_column:
            # If no explicit weight column, try to calculate it
            if 'Market_Value' in df.columns:
                total_market_value = df['Market_Value'].sum()
                df['Weight'] = df['Market_Value'] / total_market_value * 100
                weight_column = 'Weight'
            else:
                raise ValueError(f"No weight column found in {csv_filename}")
        
        # Group by industry and sum weights
        industry_allocation = df.groupby(industry_column)[weight_column].sum().reset_index()
        industry_allocation.columns = ['Industry', 'Weight']
        
    else:
        # For equity ETFs, standard processing
        weight_column = None
        for col in ['Percent_of_Fund', 'Weight', 'Market_Value']:
            if col in df.columns:
                weight_column = col
                break
                
        if not weight_column:
            # If no explicit weight column, try to calculate it
            if 'Market_Value' in df.columns:
                total_market_value = df['Market_Value'].sum()
                df['Weight'] = df['Market_Value'] / total_market_value * 100
                weight_column = 'Weight'
            else:
                raise ValueError(f"No weight column found in {csv_filename}")
            
        # Strip '%' from the 'Weight' column, only for non-empty cells
        df[weight_column] = df[weight_column].apply(lambda x: x.replace('%', '') if isinstance(x, str) and x else x)
        df[weight_column] = pd.to_numeric(df[weight_column], errors='coerce') # convert weight to numeric
        
        # Group by industry and sum weights
        industry_allocation = df.groupby(industry_column)[weight_column].sum().reset_index()
        industry_allocation.columns = ['Industry', 'Weight']
                
    # Ensure weights sum to 100%
    if not np.isclose(industry_allocation['Weight'].sum(), 100, atol=5):
        # Normalize weights to sum to 100%
        industry_allocation['Weight'] = industry_allocation['Weight'] / industry_allocation['Weight'].sum() * 100
    
    return industry_allocation

@app.route('/portfolio-industry-weightage', methods=['POST'])
def get_portfolio_industry_weightage():
    """
    Endpoint to retrieve industry allocation for a portfolio of ETFs
    
    Request JSON format:
    {
        "tickers": {
            "SPY": 0.6, 
            "BND": 0.4
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
        supported_tickers = ['SPY', 'GBTC', 'VUG', 'BRK-B', 'VYM', 'SPLV', 'USMV', 'BND', 'AGG']
        for ticker in tickers_dict.keys():
            if ticker not in supported_tickers:
                return jsonify({"error": f"Ticker {ticker} is not supported. Supported tickers: {', '.join(supported_tickers)}"}), 400
        
        # Ensure weights sum to approximately 1 (allowing for float precision)
        weights_sum = sum(tickers_dict.values())
        if not np.isclose(weights_sum, 1.0, atol=1e-2):
            return jsonify({"error": f"Weights should sum to 1, got {weights_sum}"}), 400
        
        # Load industry allocation for all tickers
        all_industry_data = {}
        for ticker, weight in tickers_dict.items():
            try:
                ticker_industry_data = load_industry_allocation_data(ticker)
                all_industry_data[ticker] = {
                    'allocation': ticker_industry_data,
                    'weight': weight
                }
            except ValueError as ve:
                return jsonify({"error": str(ve)}), 400
            except FileNotFoundError as fe:
                return jsonify({"error": str(fe)}), 404
            except Exception as e:
                return jsonify({"error": f"Error fetching industry data for {ticker}: {str(e)}"}), 500
        
        # Combine industry allocations across all ETFs in the portfolio
        combined_industries = {}
        
        for ticker, data in all_industry_data.items():
            etf_weight = data['weight']
            industry_allocation = data['allocation']
            
            for _, row in industry_allocation.iterrows():
                industry = row['Industry']
                industry_weight = row['Weight'] * etf_weight / 100  # Convert to portfolio weight
                
                if industry in combined_industries:
                    combined_industries[industry] += industry_weight
                else:
                    combined_industries[industry] = industry_weight
        
        # Convert to dataframe
        result_df = pd.DataFrame({
            'Industry': combined_industries.keys(),
            'Weight': [round(w * 100, 2) for w in combined_industries.values()]  # Convert back to percentage
        })
        
        # Sort by weight descending
        result_df = result_df.sort_values('Weight', ascending=False).reset_index(drop=True)
        
        # Prepare detailed breakdown for each ticker
        ticker_breakdown = {}
        for ticker, data in all_industry_data.items():
            industry_allocation = data['allocation']
            etf_weight = data['weight']
            
            ticker_breakdown[ticker] = {
                'weight': etf_weight,
                'industries': industry_allocation.to_dict(orient='records')
            }
        
        # Prepare final result
        result = {
            "portfolio_industry_allocation": result_df.to_dict(orient='records'),
            "ticker_breakdown": ticker_breakdown
        }
        
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
        "BRK-B": "Berkshire Hathaway Inc. Class B",
        "VYM": "Vanguard High Dividend Yield ETF",
        "SPLV": "Invesco S&P 500 Low Volatility ETF",
        "USMV": "iShares MSCI USA Min Vol Factor ETF",
        "BND": "Vanguard Total Bond Market ETF",
        "AGG": "iShares Core U.S. Aggregate Bond ETF"
    }
    
    return jsonify(available_etfs)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)  # Using a different port than getPortfolioPrice.py