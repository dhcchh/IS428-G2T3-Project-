from flask import Flask, request, jsonify
import pandas as pd
import numpy as np
from typing import Dict, Any
from datetime import datetime
import os
from flask_cors import CORS

# Create Flask application
app = Flask(__name__)
CORS(app)  

# Global variables
DATA_FILE = 'highLTetf.csv'
ETF_DF = None
MIN_DATE = None
MAX_DATE = None

def load_data():
    """Load ETF data from CSV file and set global variables"""
    global ETF_DF, MIN_DATE, MAX_DATE
    
    ETF_DF = pd.read_csv('highLTetf.csv')
    ETF_DF['Date'] = pd.to_datetime(ETF_DF['Date'])
    
    MIN_DATE = ETF_DF['Date'].min()
    MAX_DATE = ETF_DF['Date'].max()
    
    return ETF_DF

def get_date_range_data():
    """
    Get the min and max dates available in the dataset and ETF total returns.
    Ensures dates are in ISO format (YYYY-MM-DD).
    
    Returns:
        Dictionary with min_date, max_date, and etf_returns
    """
    etf_returns = {}
    for etf in ['SPY', 'GBTC', 'BRK-B', 'VUG']:
        try:
            total_return = (ETF_DF[etf].iloc[-1] / ETF_DF[etf].iloc[0] - 1) * 100
            etf_returns[etf] = round(total_return, 2)
        except Exception as e:
            etf_returns[etf] = 0.0
            print(f"Error calculating return for {etf}: {e}")
    
    # Ensure dates are formatted in ISO format (YYYY-MM-DD)
    min_date_iso = MIN_DATE.strftime('%Y-%m-%d')
    max_date_iso = MAX_DATE.strftime('%Y-%m-%d')
    
    print(f"Returning date range: min={min_date_iso}, max={max_date_iso}")
    
    return {
        "min_date": min_date_iso,
        "max_date": max_date_iso,
        "etf_returns": etf_returns
    }

def filter_data_by_date(start_date=None, end_date=None):
    """
    Filter data by date range with improved parsing.
    Ensures proper date handling regardless of input format.
    """
    global ETF_DF, MIN_DATE, MAX_DATE
    
    # Debug input dates
    print(f"Filtering data with input dates: start={start_date}, end={end_date}")
    
    # Convert string dates to timestamps if needed
    if isinstance(start_date, str):
        try:
            # Explicitly parse ISO format
            if start_date.count('-') == 2:
                # Assuming ISO format (YYYY-MM-DD)
                year, month, day = map(int, start_date.split('-'))
                start_date = pd.Timestamp(year=year, month=month, day=day)
            else:
                # Try pandas default parser
                start_date = pd.Timestamp(start_date)
        except Exception as e:
            print(f"Error parsing start_date '{start_date}': {e}")
            start_date = MIN_DATE
    elif start_date is None:
        start_date = MIN_DATE
        
    if isinstance(end_date, str):
        try:
            # Explicitly parse ISO format
            if end_date.count('-') == 2:
                # Assuming ISO format (YYYY-MM-DD)
                year, month, day = map(int, end_date.split('-'))
                end_date = pd.Timestamp(year=year, month=month, day=day)
            else:
                # Try pandas default parser
                end_date = pd.Timestamp(end_date)
        except Exception as e:
            print(f"Error parsing end_date '{end_date}': {e}")
            end_date = MAX_DATE
    elif end_date is None:
        end_date = MAX_DATE
    
    # Debug parsed dates
    print(f"Parsed dates: start={start_date}, end={end_date}")
    
    # Ensure dates are within the available range
    if start_date < MIN_DATE:
        print(f"Adjusting start_date {start_date} to MIN_DATE {MIN_DATE}")
        start_date = MIN_DATE
        
    if end_date > MAX_DATE:
        print(f"Adjusting end_date {end_date} to MAX_DATE {MAX_DATE}")
        end_date = MAX_DATE
        
    if start_date > end_date:
        print(f"Swapping dates: start={start_date}, end={end_date}")
        start_date, end_date = end_date, start_date
    
    # Filter data by date range
    mask = (ETF_DF['Date'] >= start_date) & (ETF_DF['Date'] <= end_date)
    period_df = ETF_DF.loc[mask].copy()
    
    # Debug results
    print(f"Filtered data: {len(period_df)} rows from {start_date} to {end_date}")
    
    return period_df, start_date, end_date

def calculate_portfolio_value(period_df, initial_investment, allocations):
    """Calculate portfolio value based on allocations and investment amount"""
    if len(period_df) == 0:
        return pd.DataFrame(), pd.DataFrame()  # Return empty if no data in range
    
    # Normalize ETF prices to the first date
    first_date = period_df['Date'].iloc[0]
    first_prices = {}
    for etf in ['SPY', 'GBTC', 'BRK-B', 'VUG']:
        first_prices[etf] = period_df.loc[period_df['Date'] == first_date, etf].values[0]
    
    # Calculate values based on allocations
    for etf in ['SPY', 'GBTC', 'BRK-B', 'VUG']:
        # Skip if allocation is 0
        if allocations.get(etf, 0) == 0:
            period_df[f'{etf}_value'] = 0
            continue
            
        # Calculate normalized return (handle potential NaN values)
        if first_prices[etf] > 0:
            period_df[f'{etf}_norm'] = period_df[etf] / first_prices[etf]
        else:
            period_df[f'{etf}_norm'] = 1.0  # Default to no change if first price is 0 or negative
        
        # Calculate value based on allocation
        etf_investment = initial_investment * (allocations[etf] / 100)
        period_df[f'{etf}_value'] = etf_investment * period_df[f'{etf}_norm']
    
    # Calculate total portfolio value
    period_df['total_value'] = (
        period_df['SPY_value'] + 
        period_df['GBTC_value'] + 
        period_df['BRK-B_value'] + 
        period_df['VUG_value']
    )
    
    # Calculate daily and cumulative returns
    period_df['daily_return'] = period_df['total_value'].pct_change()
    period_df['cumulative_return'] = (period_df['total_value'] / period_df['total_value'].iloc[0]) - 1
    
    # Calculate drawdown
    period_df['peak_value'] = period_df['total_value'].cummax()
    period_df['drawdown'] = (period_df['total_value'] - period_df['peak_value']) / period_df['peak_value']
    
    # Calculate yearly returns
    period_df['year'] = period_df['Date'].dt.year
    yearly_returns = period_df.groupby('year')['total_value'].apply(
        lambda x: (x.iloc[-1] / x.iloc[0]) - 1 if len(x) > 1 else 0
    ).reset_index()
    yearly_returns.columns = ['year', 'yearly_return']
    
    # Convert date to string for JSON serialization
    period_df['Date'] = period_df['Date'].dt.strftime('%Y-%m-%d')
    
    return period_df, yearly_returns

def calculate_risk_metrics(portfolio_df):
    """Calculate various risk and return metrics"""
    if len(portfolio_df) == 0:
        return {}
        
    # Basic metrics
    initial_value = portfolio_df['total_value'].iloc[0]
    final_value = portfolio_df['total_value'].iloc[-1]
    total_return = (final_value / initial_value) - 1
    
    # Time period in years for annualization
    start_date = pd.to_datetime(portfolio_df['Date'].iloc[0])
    end_date = pd.to_datetime(portfolio_df['Date'].iloc[-1])
    days = (end_date - start_date).days
    years = days / 365.25
    
    # Annualized return
    annualized_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0
    
    # Volatility (annualized standard deviation of returns)
    daily_std = portfolio_df['daily_return'].std()
    annualized_volatility = daily_std * np.sqrt(252) if not pd.isna(daily_std) else 0
    
    # Maximum drawdown
    max_drawdown = portfolio_df['drawdown'].min()
    
    # Sharpe ratio (assuming risk-free rate of 0.02)
    risk_free_rate = 0.02
    sharpe_ratio = (annualized_return - risk_free_rate) / annualized_volatility if annualized_volatility > 0 else 0
    
    # Risk level based on volatility
    if annualized_volatility < 0.05:
        risk_level = "Very Low"
    elif annualized_volatility < 0.10:
        risk_level = "Low"
    elif annualized_volatility < 0.15:
        risk_level = "Moderate"
    elif annualized_volatility < 0.20:
        risk_level = "High"
    else:
        risk_level = "Very High"
    
    return {
        'initial_value': float(initial_value),
        'final_value': float(final_value),
        'total_return': float(total_return),
        'annualized_return': float(annualized_return),
        'max_drawdown': float(max_drawdown),
        'volatility': float(annualized_volatility),
        'risk_level': risk_level,
        'sharpe_ratio': float(sharpe_ratio),
        'years': float(years)
    }

def calculate_etf_performance(period_df):
    """Calculate performance data for individual ETFs"""
    etf_performance = {}
    for etf in ['SPY', 'GBTC', 'BRK-B', 'VUG']:
        if etf not in period_df.columns:
            continue
            
        # First price and last price
        first_price = float(period_df[etf].iloc[0])
        last_price = float(period_df[etf].iloc[-1])
        
        # Calculate total return
        total_return = (last_price / first_price) - 1
        
        # Calculate volatility
        returns = pd.to_numeric(period_df[etf]).pct_change().dropna()
        volatility = returns.std() * np.sqrt(252)
        
        # Store results
        etf_performance[etf] = {
            'first_price': first_price,
            'last_price': last_price,
            'total_return': float(total_return),
            'volatility': float(volatility)
        }
    
    return etf_performance

def process_request_data():
    """Process request data common to multiple endpoints"""
    data = request.get_json()
    if not data:
        return None, jsonify({"error": "No data provided"}), 400
    
    # Extract parameters
    initial_investment = float(data.get('initial_investment', 10000))
    allocations = data.get('allocations', {
        'SPY': 25,
        'GBTC': 25, 
        'BRK-B': 25, 
        'VUG': 25
    })
    
    # Validate allocations
    total_allocation = sum(allocations.values())
    if abs(total_allocation - 100) > 0.01:  # Allow a small tolerance for floating-point errors
        return None, jsonify({"error": f"Total allocation must be 100%, got {total_allocation}%"}), 400
        
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    
    # Filter data by date
    period_df, start_date, end_date = filter_data_by_date(start_date, end_date)
    
    if len(period_df) == 0:
        return None, jsonify({"error": "No data available for the specified date range"}), 400
    
    # Calculate portfolio values
    portfolio_df, yearly_returns = calculate_portfolio_value(
        period_df,
        initial_investment=initial_investment,
        allocations=allocations
    )
    
    return {
        'portfolio_df': portfolio_df,
        'yearly_returns': yearly_returns,
        'initial_investment': initial_investment,
        'allocations': allocations,
        'start_date': start_date,
        'end_date': end_date
    }, None, None

def safe_json_serialization(obj):
    """Convert NaN values to null for JSON serialization"""
    if isinstance(obj, dict):
        return {k: safe_json_serialization(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [safe_json_serialization(item) for item in obj]
    elif isinstance(obj, float) and (np.isnan(obj) or np.isinf(obj)):
        return None
    else:
        return obj

# API Endpoints
@app.route('/api/date-range', methods=['GET'])
def get_date_range():
    """API endpoint to get available date range and ETF returns"""
    try:
        data_range = get_date_range_data()
        return jsonify(data_range)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/portfolio-value', methods=['POST'])
def get_final_portfolio_value():
    """API endpoint to get final portfolio value"""
    try:
        result, error, status = process_request_data()
        if error:
            return error, status
        
        portfolio_df = result['portfolio_df']
        
        final_value = float(portfolio_df['total_value'].iloc[-1])
        initial_value = float(portfolio_df['total_value'].iloc[0])
        
        return jsonify({
            "initial_value": initial_value,
            "final_value": final_value,
            "growth_amount": final_value - initial_value,
            "growth_percentage": ((final_value / initial_value) - 1) * 100
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/total-return', methods=['POST'])
def get_total_return():
    """API endpoint to get total return metrics"""
    try:
        result, error, status = process_request_data()
        if error:
            return error, status
        
        portfolio_df = result['portfolio_df']
        metrics = calculate_risk_metrics(portfolio_df)
        
        return jsonify({
            "total_return": metrics['total_return'],
            "annualized_return": metrics['annualized_return'],
            "years": metrics['years'],
            "sharpe_ratio": metrics['sharpe_ratio']
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/max-drawdown', methods=['POST'])
def get_max_drawdown():
    """API endpoint to get maximum drawdown"""
    try:
        result, error, status = process_request_data()
        if error:
            return error, status
        
        portfolio_df = result['portfolio_df']
        
        # Find the max drawdown and when it occurred
        max_drawdown = portfolio_df['drawdown'].min()
        max_drawdown_date = portfolio_df.loc[portfolio_df['drawdown'] == max_drawdown, 'Date'].values[0]
        
        return jsonify({
            "max_drawdown": float(max_drawdown),
            "max_drawdown_percentage": float(max_drawdown) * 100,
            "max_drawdown_date": max_drawdown_date
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/risk-level', methods=['POST'])
def get_risk_level():
    """API endpoint to get risk level and volatility metrics"""
    try:
        result, error, status = process_request_data()
        if error:
            return error, status
        
        portfolio_df = result['portfolio_df']
        metrics = calculate_risk_metrics(portfolio_df)
        
        return jsonify({
            "risk_level": metrics['risk_level'],
            "volatility": metrics['volatility'],
            "volatility_percentage": metrics['volatility'] * 100,
            "sharpe_ratio": metrics['sharpe_ratio']
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/portfolio-growth', methods=['POST'])
def get_portfolio_growth():
    """API endpoint to get portfolio growth data for visualization"""
    try:
        result, error, status = process_request_data()
        if error:
            return error, status
        
        portfolio_df = result['portfolio_df'].copy()
        
        # Simplify for visualization purposes
        growth_data = portfolio_df[['Date', 'total_value', 'cumulative_return']].copy()
        
        # Convert to percentage for cumulative return
        growth_data['cumulative_return_percentage'] = growth_data['cumulative_return'] * 100
        
        return jsonify({
            "portfolio_growth": growth_data.to_dict(orient='records')
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/drawdown-analysis', methods=['POST'])
def get_drawdown_analysis():
    """API endpoint to get drawdown analysis data"""
    try:
        result, error, status = process_request_data()
        if error:
            return error, status
        
        portfolio_df = result['portfolio_df'].copy()
        
        # Drawdown analysis data
        drawdown_data = portfolio_df[['Date', 'total_value', 'peak_value', 'drawdown']].copy()
        
        # Convert drawdown to percentage
        drawdown_data['drawdown_percentage'] = drawdown_data['drawdown'] * 100
        
        # Count severe drawdowns (greater than 10%)
        severe_drawdowns = len(drawdown_data[drawdown_data['drawdown'] < -0.1])
        
        # Find recovery periods
        drawdown_periods = []
        in_drawdown = False
        start_idx = 0
        
        for i, row in drawdown_data.iterrows():
            if not in_drawdown and row['drawdown'] < -0.05:
                # Start of new drawdown period (5% threshold)
                in_drawdown = True
                start_idx = i
            elif in_drawdown and row['drawdown'] >= -0.01:
                # End of drawdown period (recovered to within 1%)
                in_drawdown = False
                drawdown_periods.append({
                    'start_date': drawdown_data.loc[start_idx, 'Date'],
                    'end_date': row['Date'],
                    'max_drawdown': float(drawdown_data.loc[start_idx:i, 'drawdown'].min()),
                    'recovery_days': (i - start_idx)
                })
        
        return jsonify({
            "drawdown_data": drawdown_data.to_dict(orient='records'),
            "max_drawdown": float(drawdown_data['drawdown'].min()),
            "severe_drawdowns": severe_drawdowns,
            "drawdown_periods": drawdown_periods
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/etf-comparison', methods=['POST'])
def get_etf_comparison():
    """API endpoint to get ETF comparison data"""
    try:
        result, error, status = process_request_data()
        if error:
            return error, status
        
        portfolio_df = result['portfolio_df'].copy()
        allocations = result['allocations']
        
        # Calculate ETF performance
        etf_performance = calculate_etf_performance(portfolio_df)
        
        # Prepare normalized performance data for visualization
        normalized_data = []
        
        for date_idx, row in portfolio_df.iterrows():
            date_entry = {'Date': row['Date']}
            for etf in ['SPY', 'GBTC', 'BRK-B', 'VUG']:
                if allocations.get(etf, 0) > 0:
                    date_entry[f'{etf}_normalized'] = float(row[f'{etf}_norm'])
            normalized_data.append(date_entry)
        
        return jsonify({
            "etf_performance": etf_performance,
            "normalized_data": normalized_data,
            "allocations": allocations
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/yearly-returns', methods=['POST'])
def get_yearly_returns():
    """API endpoint to get yearly returns data"""
    try:
        result, error, status = process_request_data()
        if error:
            return error, status
        
        yearly_returns = result['yearly_returns']
        
        # Add percentage format
        yearly_returns['yearly_return_percentage'] = yearly_returns['yearly_return'] * 100
        
        # Calculate average yearly return
        avg_yearly_return = yearly_returns['yearly_return'].mean()
        
        # Calculate positive and negative years
        positive_years = len(yearly_returns[yearly_returns['yearly_return'] > 0])
        negative_years = len(yearly_returns[yearly_returns['yearly_return'] < 0])
        
        # Calculate best and worst years
        best_year = int(yearly_returns.loc[yearly_returns['yearly_return'].idxmax(), 'year'])
        best_return = float(yearly_returns['yearly_return'].max())
        
        worst_year = int(yearly_returns.loc[yearly_returns['yearly_return'].idxmin(), 'year'])
        worst_return = float(yearly_returns['yearly_return'].min())
        
        return jsonify({
            "yearly_returns": yearly_returns.to_dict(orient='records'),
            "avg_yearly_return": float(avg_yearly_return),
            "avg_yearly_return_percentage": float(avg_yearly_return) * 100,
            "positive_years": positive_years,
            "negative_years": negative_years,
            "best_year": best_year,
            "best_return": best_return,
            "best_return_percentage": best_return * 100,
            "worst_year": worst_year,
            "worst_return": worst_return,
            "worst_return_percentage": worst_return * 100
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/calculate-all', methods=['POST'])
def calculate_all():
    """API endpoint to calculate all portfolio metrics at once with improved error handling"""
    try:
        result, error, status = process_request_data()
        if error:
            return error, status
        
        portfolio_df = result['portfolio_df']
        yearly_returns = result['yearly_returns']
        
        # Verify we have valid data
        if len(portfolio_df) < 2:
            return jsonify({
                "error": "Insufficient data points for the selected time period"
            }), 400
        
        # Calculate metrics
        metrics = calculate_risk_metrics(portfolio_df)
        
        # Calculate ETF performance
        etf_performance = calculate_etf_performance(portfolio_df)
        
        # Convert DataFrames to lists of dictionaries for JSON serialization
        portfolio_data = portfolio_df.to_dict(orient='records')
        yearly_data = yearly_returns.to_dict(orient='records')
        
        # Add time period information to the response
        response = {
            "metrics": metrics,
            "etf_performance": etf_performance,
            "portfolio_data": portfolio_data,
            "yearly_returns": yearly_data,
            "time_period": {
                "start_date": result['start_date'].strftime('%Y-%m-%d') if isinstance(result['start_date'], pd.Timestamp) else result['start_date'],
                "end_date": result['end_date'].strftime('%Y-%m-%d') if isinstance(result['end_date'], pd.Timestamp) else result['end_date'],
                "days": (result['end_date'] - result['start_date']).days if isinstance(result['start_date'], pd.Timestamp) and isinstance(result['end_date'], pd.Timestamp) else None
            }
        }
        
        # Return all results with NaN handling
        return jsonify(safe_json_serialization(response))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        import traceback
        print("Error in calculate_all:", traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "ok"})

# Initialize data at startup - Flask 2.x removed before_first_request
with app.app_context():
    load_data()

if __name__ == "__main__":
    # Load data at startup
    load_data()
    
    # Run the Flask application
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)