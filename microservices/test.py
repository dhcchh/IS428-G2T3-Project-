import requests
import pandas as pd
import matplotlib.pyplot as plt
import json

# API endpoint
url = "http://localhost:5000/portfolio-data"

# Define portfolio with tickers and weights - equal weight to all four assets
portfolio = {
    "tickers": {
        "SPY": 0.25,    # S&P 500
        "GBTC": 0.25,   # Bitcoin Trust
        "VUG": 0.25,    # Vanguard Growth
        "BRK-B": 0.25   # Berkshire Hathaway
    }
}

print("Sending request to portfolio microservice...")
print(f"Portfolio: {json.dumps(portfolio, indent=2)}")

# Make the API request
response = requests.post(url, json=portfolio)

if response.status_code == 200:
    data = response.json()
    
    # Convert portfolio data to DataFrame
    portfolio_df = pd.DataFrame(data['portfolio_data'])
    portfolio_df['date'] = pd.to_datetime(portfolio_df['date'])
    portfolio_df.set_index('date', inplace=True)
    
    print("\nSuccessfully retrieved portfolio data!")
    print(f"Data range: {portfolio_df.index.min().strftime('%Y-%m-%d')} to {portfolio_df.index.max().strftime('%Y-%m-%d')}")
    print(f"Number of data points: {len(portfolio_df)}")
    
    # Plot the portfolio performance along with individual components
    plt.figure(figsize=(12, 6))
    
    # Plot the portfolio value
    plt.plot(portfolio_df.index, portfolio_df['portfolio_value'], 'k-', linewidth=2, label='Portfolio')
    
    # Plot each component
    colors = ['b', 'r', 'g', 'orange']
    for i, ticker in enumerate(portfolio['tickers'].keys()):
        component_data = pd.DataFrame(data['component_data'][ticker])
        component_data['date'] = pd.to_datetime(component_data['date'])
        component_data.set_index('date', inplace=True)
        plt.plot(component_data.index, component_data['normalized_price'], 
                 color=colors[i % len(colors)], linestyle='-', linewidth=1, alpha=0.7,
                 label=ticker)
    
    plt.title('Portfolio Performance (Normalized)')
    plt.xlabel('Date')
    plt.ylabel('Value (Starting at 1.0)')
    plt.grid(True, alpha=0.3)
    plt.legend(loc='upper left')
    plt.tight_layout()
    plt.savefig('portfolio_performance.png')
    print("\nSaved performance chart to 'portfolio_performance.png'")
    
    # Calculate some statistics
    initial_value = 1.0  # By definition of our normalization
    final_value = portfolio_df['portfolio_value'].iloc[-1]
    percent_change = (final_value - initial_value) / initial_value * 100
    
    print("\nPerformance Summary:")
    print(f"Initial value: {initial_value:.4f}")
    print(f"Final value: {final_value:.4f}")
    print(f"Total return: {percent_change:.2f}%")
    
    # More detailed analysis of individual components
    print("\nComponent Performance:")
    for ticker in portfolio['tickers'].keys():
        ticker_data = pd.DataFrame(data['component_data'][ticker])
        ticker_data['date'] = pd.to_datetime(ticker_data['date'])
        ticker_data.set_index('date', inplace=True)
        
        print(f"\n{ticker} Price Data:")
        print(f"Initial price: ${ticker_data['price'].iloc[0]:.2f}")
        print(f"Final price: ${ticker_data['price'].iloc[-1]:.2f}")
        price_change = (ticker_data['price'].iloc[-1] - ticker_data['price'].iloc[0]) / ticker_data['price'].iloc[0] * 100
        print(f"Percent change: {price_change:.2f}%")
        
    # Calculate correlation matrix between components
    correlation_data = {}
    for ticker in portfolio['tickers'].keys():
        ticker_data = pd.DataFrame(data['component_data'][ticker])
        ticker_data['date'] = pd.to_datetime(ticker_data['date'])
        ticker_data.set_index('date', inplace=True)
        correlation_data[ticker] = ticker_data['normalized_price']
    
    correlation_df = pd.DataFrame(correlation_data)
    print("\nCorrelation Matrix:")
    print(correlation_df.corr().round(2))
    
else:
    print(f"Error: {response.status_code}")
    print(response.json())