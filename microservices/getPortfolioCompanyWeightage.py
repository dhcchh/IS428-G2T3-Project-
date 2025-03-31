from flask import Flask, request, jsonify
import pandas as pd
import numpy as np
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

def load_company_allocation_data(ticker):
    """
    Load company allocation data from CSV files
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
        'AGG': '../mavis datasets/agg_share_allocation.csv'
    }
    
    # Check if ticker is supported
    if ticker not in ticker_file_map:
        raise ValueError(f"Company allocation for {ticker} not available. Supported tickers: {', '.join(ticker_file_map.keys())}")
    
    csv_filename = ticker_file_map[ticker]
    
    if not os.path.exists(csv_filename):
        raise FileNotFoundError(f"CSV file not found: {csv_filename}")
    
    # Read the CSV file
    df = pd.read_csv(csv_filename)
    
    # Determine the company/holdings column
    company_column = None
    for col in ['Holdings', 'Company', 'Name', 'Security']:
        if col in df.columns:
            company_column = col
            break
    
    if not company_column:
        raise ValueError(f"No company/holdings column found in {csv_filename}")
    
    # For bond ETFs (BND, AGG), use different processing if needed
    if ticker in ['BND', 'AGG']:
        # Check for weight column
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
        
        # Filter out any rows with missing company information
        df = df[df[company_column].notna() & (df[company_column] != '--')]
        
        # Select relevant columns
        company_allocation = df[[company_column, weight_column]].copy()
        company_allocation.columns = ['Company', 'Weight']
        
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
        
        # Filter out any rows with missing company information
        df = df[df[company_column].notna() & (df[company_column] != '--')]
        
        # Select relevant columns
        company_allocation = df[[company_column, weight_column]].copy()
        company_allocation.columns = ['Company', 'Weight']
    
    # Get ticker column if available
    ticker_column = None
    for col in ['Ticker', 'Symbol']:
        if col in df.columns:
            ticker_column = col
            break
    
    if ticker_column:
        company_allocation['Symbol'] = df[ticker_column]
    
    # Add sector/industry if available
    sector_column = None
    for col in ['Sector', 'Industry', 'Category']:
        if col in df.columns:
            sector_column = col
            break
    
    if sector_column:
        company_allocation['Sector'] = df[sector_column]
    
    # Sort by weight descending
    company_allocation = company_allocation.sort_values('Weight', ascending=False).reset_index(drop=True)
    
    return company_allocation

@app.route('/portfolio-company-weightage', methods=['POST'])
def get_portfolio_company_weightage():
    """
    Endpoint to retrieve company allocation for a portfolio of ETFs
    
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
        
        # Load company allocation for all tickers
        all_company_data = {}
        for ticker, weight in tickers_dict.items():
            try:
                ticker_company_data = load_company_allocation_data(ticker)
                all_company_data[ticker] = {
                    'allocation': ticker_company_data,
                    'weight': weight
                }
            except ValueError as ve:
                return jsonify({"error": str(ve)}), 400
            except FileNotFoundError as fe:
                return jsonify({"error": str(fe)}), 404
            except Exception as e:
                return jsonify({"error": f"Error fetching company data for {ticker}: {str(e)}"}), 500
        
        # Combine company allocations across all ETFs in the portfolio
        # Create a dictionary to track combined company weights
        combined_companies = {}
        company_details = {}  # Store additional details about each company
        
        for ticker, data in all_company_data.items():
            etf_weight = data['weight']
            company_allocation = data['allocation']
            
            for _, row in company_allocation.iterrows():
                company = row['Company']
                company_weight = row['Weight'] * etf_weight / 100  # Convert to portfolio weight
                
                # Update combined weight
                if company in combined_companies:
                    combined_companies[company] += company_weight
                else:
                    combined_companies[company] = company_weight
                    # Initialize company details
                    company_details[company] = {
                        'etfs': [],
                        'sector': row.get('Sector', 'Unknown'),
                        'symbol': row.get('Symbol', '')
                    }
                
                # Add this ETF to the company's ETF list
                if ticker not in company_details[company]['etfs']:
                    company_details[company]['etfs'].append(ticker)
        
        # Convert to dataframe and include details
        result_data = []
        for company, weight in combined_companies.items():
            result_data.append({
                'Company': company,
                'Weight': round(weight * 100, 3),  # Convert back to percentage
                'Sector': company_details[company]['sector'],
                'Symbol': company_details[company]['symbol'],
                'ETFs': ', '.join(company_details[company]['etfs'])
            })
        
        # Create result dataframe
        result_df = pd.DataFrame(result_data)
        
        # Sort by weight descending
        result_df = result_df.sort_values('Weight', ascending=False).reset_index(drop=True)
        
        # Limit to top companies (e.g., top 50)
        top_companies = result_df.head(50)
        
        # Calculate "Others" category for the rest
        if len(result_df) > 50:
            others_weight = result_df.iloc[50:]['Weight'].sum()
            others_row = {
                'Company': 'Others',
                'Weight': others_weight,
                'Sector': 'Various',
                'Symbol': '',
                'ETFs': ''
            }
            top_companies = pd.concat([top_companies, pd.DataFrame([others_row])], ignore_index=True)
        
        # Prepare detailed breakdown for each ticker
        ticker_breakdown = {}
        for ticker, data in all_company_data.items():
            company_allocation = data['allocation']
            etf_weight = data['weight']
            
            ticker_breakdown[ticker] = {
                'weight': etf_weight,
                'companies': company_allocation.to_dict(orient='records')
            }
        
        # Prepare final result
        result = {
            "portfolio_company_allocation": top_companies.to_dict(orient='records'),
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
    app.run(debug=True, host='0.0.0.0', port=5002)  # Using a different port than the other microservices