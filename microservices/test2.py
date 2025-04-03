import requests
import json
from pprint import pprint

# Base URL for the API
BASE_URL = "http://localhost:5001"

def test_date_range():
    """Test the date range endpoint"""
    print("\n=== Testing Date Range Endpoint ===")
    response = requests.get(f"{BASE_URL}/api/date-range")
    
    if response.status_code == 200:
        pprint(response.json())
        print("✓ Date range test successful")
    else:
        print(f"✗ Error: {response.status_code} - {response.text}")
        
def test_portfolio_value():
    """Test the portfolio value endpoint"""
    print("\n=== Testing Portfolio Value Endpoint ===")
    
    payload = {
        "initial_investment": 10000,
        "allocations": {
            "SPY": 60,
            "BND": 20,
            "VTIP": 10,
            "VXUS": 10
        },
        "start_date": "2018-01-01",
        "end_date": "2022-12-31"
    }
    
    response = requests.post(f"{BASE_URL}/api/portfolio-value", json=payload)
    
    if response.status_code == 200:
        pprint(response.json())
        print("✓ Portfolio value test successful")
    else:
        print(f"✗ Error: {response.status_code} - {response.text}")

def test_total_return():
    """Test the total return endpoint"""
    print("\n=== Testing Total Return Endpoint ===")
    
    payload = {
        "initial_investment": 10000,
        "allocations": {
            "SPY": 60,
            "BND": 20,
            "VTIP": 10,
            "VXUS": 10
        },
        "start_date": "2018-01-01",
        "end_date": "2022-12-31"
    }
    
    response = requests.post(f"{BASE_URL}/api/total-return", json=payload)
    
    if response.status_code == 200:
        pprint(response.json())
        print("✓ Total return test successful")
    else:
        print(f"✗ Error: {response.status_code} - {response.text}")

def test_max_drawdown():
    """Test the maximum drawdown endpoint"""
    print("\n=== Testing Maximum Drawdown Endpoint ===")
    
    payload = {
        "initial_investment": 10000,
        "allocations": {
            "SPY": 60,
            "BND": 20,
            "VTIP": 10,
            "VXUS": 10
        },
        "start_date": "2018-01-01",
        "end_date": "2022-12-31"
    }
    
    response = requests.post(f"{BASE_URL}/api/max-drawdown", json=payload)
    
    if response.status_code == 200:
        pprint(response.json())
        print("✓ Max drawdown test successful")
    else:
        print(f"✗ Error: {response.status_code} - {response.text}")

def test_risk_level():
    """Test the risk level endpoint"""
    print("\n=== Testing Risk Level Endpoint ===")
    
    payload = {
        "initial_investment": 10000,
        "allocations": {
            "SPY": 60,
            "BND": 20,
            "VTIP": 10,
            "VXUS": 10
        },
        "start_date": "2018-01-01",
        "end_date": "2022-12-31"
    }
    
    response = requests.post(f"{BASE_URL}/api/risk-level", json=payload)
    
    if response.status_code == 200:
        pprint(response.json())
        print("✓ Risk level test successful")
    else:
        print(f"✗ Error: {response.status_code} - {response.text}")

def test_portfolio_growth():
    """Test the portfolio growth endpoint"""
    print("\n=== Testing Portfolio Growth Endpoint ===")
    
    payload = {
        "initial_investment": 10000,
        "allocations": {
            "SPY": 60,
            "BND": 20,
            "VTIP": 10,
            "VXUS": 10
        },
        "start_date": "2018-01-01",
        "end_date": "2022-12-31"
    }
    
    response = requests.post(f"{BASE_URL}/api/portfolio-growth", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print(f"Number of data points: {len(data['portfolio_growth'])}")
        print("First data point:")
        pprint(data['portfolio_growth'][0])
        print("Last data point:")
        pprint(data['portfolio_growth'][-1])
        print("✓ Portfolio growth test successful")
    else:
        print(f"✗ Error: {response.status_code} - {response.text}")

def test_drawdown_analysis():
    """Test the drawdown analysis endpoint"""
    print("\n=== Testing Drawdown Analysis Endpoint ===")
    
    payload = {
        "initial_investment": 10000,
        "allocations": {
            "SPY": 60,
            "BND": 20,
            "VTIP": 10,
            "VXUS": 10
        },
        "start_date": "2018-01-01",
        "end_date": "2022-12-31"
    }
    
    response = requests.post(f"{BASE_URL}/api/drawdown-analysis", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print(f"Max drawdown: {data['max_drawdown']}")
        print(f"Severe drawdowns: {data['severe_drawdowns']}")
        print(f"Drawdown periods: {len(data['drawdown_periods'])}")
        print("✓ Drawdown analysis test successful")
    else:
        print(f"✗ Error: {response.status_code} - {response.text}")

def test_etf_comparison():
    """Test the ETF comparison endpoint"""
    print("\n=== Testing ETF Comparison Endpoint ===")
    
    payload = {
        "initial_investment": 10000,
        "allocations": {
            "SPY": 60,
            "BND": 20,
            "VTIP": 10,
            "VXUS": 10
        },
        "start_date": "2018-01-01",
        "end_date": "2022-12-31"
    }
    
    response = requests.post(f"{BASE_URL}/api/etf-comparison", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print("ETF Performance:")
        pprint(data['etf_performance'])
        print("✓ ETF comparison test successful")
    else:
        print(f"✗ Error: {response.status_code} - {response.text}")

def test_yearly_returns():
    """Test the yearly returns endpoint"""
    print("\n=== Testing Yearly Returns Endpoint ===")
    
    payload = {
        "initial_investment": 10000,
        "allocations": {
            "SPY": 60,
            "BND": 20,
            "VTIP": 10,
            "VXUS": 10
        },
        "start_date": "2018-01-01",
        "end_date": "2022-12-31"
    }
    
    response = requests.post(f"{BASE_URL}/api/yearly-returns", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print(f"Average yearly return: {data['avg_yearly_return_percentage']}%")
        print(f"Positive years: {data['positive_years']}")
        print(f"Negative years: {data['negative_years']}")
        print(f"Best year ({data['best_year']}): {data['best_return_percentage']}%")
        print(f"Worst year ({data['worst_year']}): {data['worst_return_percentage']}%")
        print("✓ Yearly returns test successful")
    else:
        print(f"✗ Error: {response.status_code} - {response.text}")

def test_calculate_all():
    """Test the calculate all endpoint"""
    print("\n=== Testing Calculate All Endpoint ===")
    
    payload = {
        "initial_investment": 10000,
        "allocations": {
            "SPY": 60,
            "BND": 20,
            "VTIP": 10,
            "VXUS": 10
        },
        "start_date": "2018-01-01",
        "end_date": "2022-12-31"
    }
    
    response = requests.post(f"{BASE_URL}/api/calculate-all", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print("Metrics:")
        pprint(data['metrics'])
        print("✓ Calculate all test successful")
    else:
        print(f"✗ Error: {response.status_code} - {response.text}")

def test_health():
    """Test the health check endpoint"""
    print("\n=== Testing Health Check Endpoint ===")
    
    response = requests.get(f"{BASE_URL}/health")
    
    if response.status_code == 200:
        pprint(response.json())
        print("✓ Health check test successful")
    else:
        print(f"✗ Error: {response.status_code} - {response.text}")

if __name__ == "__main__":
    print("Starting API tests...")
    
    try:
        # Test health check first
        test_health()
        
        # Test other endpoints
        test_date_range()
        test_portfolio_value()
        test_total_return()
        test_max_drawdown()
        test_risk_level()
        test_portfolio_growth()
        test_drawdown_analysis()
        test_etf_comparison()
        test_yearly_returns()
        test_calculate_all()
        
        print("\nAll tests completed.")
    except requests.exceptions.ConnectionError:
        print("\n✗ Connection error: Make sure the API server is running at", BASE_URL)