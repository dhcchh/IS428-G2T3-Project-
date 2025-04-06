
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

### Steps to Install

1. **Clone this repository**:
   ```bash
   git clone https://github.com/your-username/IS428-G2T3-Project.git
   ```

2. **Install dependencies** for microservices:
   Navigate to the `microservices` folder and install the required libraries.
   ```bash
   cd microservices
   pip install -r requirements.txt
   ```

3. **Start the Flask microservices**:
   Run the Python Flask microservices that are necessary to fetch and process data.
   ```bash
   flask run
   ```

4. **Open the visualizations**:
   To open the visualizations, copy the file path of any HTML file (e.g., `index.html`) into your browser's address bar.

## Usage

1. **index.html**: Open `index.html` to view the first set of visualizations and a user interface for portfolio selection.
2. **Portfolio Pages**: From the index page, users can click buttons to navigate to portfolio-specific HTML pages.
3. **Microservices**: Ensure that the microservices are running in the background to fetch and process financial data.

### Example:
- Visit `localhost:5000/index.html` to interact with the main dashboard.
- Navigate to a specific portfolio to see recommended ETFs and tailored visualizations.

## Contributing

We welcome contributions! If you'd like to contribute to this project, please follow these steps:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Make your changes and commit them (`git commit -am 'Add new feature'`).
4. Push to the branch (`git push origin feature-branch`).
5. Open a pull request.

## Acknowledgements

- **Tableau**: For creating powerful and interactive dashboards.
- **D3.js**: For dynamic and interactive visualizations.
- **Python**: For backend data processing and API calls to external financial data services.
- **yfinance**: For fetching financial market data.
