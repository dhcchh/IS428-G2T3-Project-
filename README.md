
# IS428 - Inflation Hedge through ETF Investments

This project explores the long-term advantages of investing in Exchange-Traded Funds (ETFs) compared to traditional savings in the context of rising inflation. It includes visualizations, a portfolio matching system, and dynamic analysis tools aimed at helping users make informed investment decisions. The system is designed to provide personalized recommendations for portfolios based on risk tolerance, investment volume, and time horizon.

## Table of Contents

- [Project Overview](#project-overview)
- [Installation Instructions](#installation-instructions)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgements](#acknowledgements)

## Project Overview

This repository contains the following:

- **index.html**: The main page with two visualizations and a navigation system directing users to various portfolio pages.
- **Portfolio Pages**: Each portfolio HTML page showcases four ETFs suited for specific portfolios and includes separate visualizations for each.
- **Microservices**: Python Flask-based microservices necessary for data processing, fetching, and handling.

The goal is to illustrate how strategic investing can hedge against inflation, empowering users to make data-driven decisions about their financial future. The visualizations are powered by Tableau and D3.js, while Python manages backend data processing.

## Installation Instructions

To run this project locally, you'll need to set up a few microservices and ensure the system can handle the visualizations.

### Prerequisites
- Python 3.x
- Flask
- Required Python libraries (to be installed via `requirements.txt`)

# Portfolio Visualization Application

This project consists of a d3.js web application frontend with multiple Python microservices backend for portfolio data analysis and visualization.

## Prerequisites

- Python 3.x
- pip (Python package installer)
- Web browser

## Setup Instructions

1. Clone or download this repository
   ```bash
   git clone [repository-url]
   cd [folder-name]
   ```

2. Create and activate a virtual environment
   ```bash
   # Create virtual environment
   python -m venv venv
   
   # Activate virtual environment
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install required dependencies
   ```bash
   pip install -r requirements.txt
   ```

## Running the Microservices

Navigate to the microservices directory:
```bash
cd microservices
```

You need to run each microservice in a separate terminal window. Make sure to activate the virtual environment in each terminal before running the microservices.

The following microservices need to be running:

| Port | Microservice | Description |
|------|-------------|-------------|
| 5000 | getPortfolioHighLT.py | Long-term high performers in portfolio |
| 5001 | getPortfolioHighST.py | Short-term high performers in portfolio |
| 5002 | getPortfolioLowLT.py | Long-term low performers in portfolio |
| 5003 | getPortfolioLowST.py | Short-term low performers in portfolio |
| 5004 | getPortfolioCompanyWeightage.py | Company weightage in portfolio |
| 5005 | getVisualisationData.py | Main visualization data (index) |
| 5006 | getPortfolioIndustryWeightage.py | Industry weightage in portfolio |
| 5007 | getCandlestickinfo.py | Candlestick chart data |
| 5008 | getPortfolioVolume.py | Portfolio volume information |
| 5009 | getPortfolioCorrelation.py | Correlation between portfolio stocks |

To run each microservice, open a separate terminal, navigate to the microservices directory, activate the virtual environment, and run the Python script:

```bash
# Example for the first microservice (repeat for each)
python getPortfolioHighLT.py
```

## Running the Web Application

Once all microservices are running, open the main HTML file in your web browser:

```bash
# Simply open index.html in your browser
# For example, on macOS
open index.html
# Or on Windows, you can double-click the file or use:
start index.html
```

## Application Structure

- `index.html`: Main entry point for the web application
- `microservices/`: Directory containing all Python microservices
  - `getPortfolioHighLT.py`: Long-term high performers (Port 5000)
  - `getPortfolioHighST.py`: Short-term high performers (Port 5001)
  - `getPortfolioLowLT.py`: Long-term low performers (Port 5002)
  - `getPortfolioLowST.py`: Short-term low performers (Port 5003)
  - `getPortfolioCompanyWeightage.py`: Company weightage (Port 5004)
  - `getVisualisationData.py`: Main visualization data (Port 5005)
  - `getPortfolioIndustryWeightage.py`: Industry weightage (Port 5006)
  - `getCandlestickinfo.py`: Candlestick chart data (Port 5007)
  - `getPortfolioVolume.py`: Portfolio volume information (Port 5008)
  - `getPortfolioCorrelation.py`: Portfolio correlation data (Port 5009)

## Acknowledgements

- **Tableau**: For creating powerful and interactive dashboards.
- **D3.js**: For dynamic and interactive visualizations.
- **Python**: For backend data processing and API calls to external financial data services.
- **yfinance**: For fetching financial market data.
