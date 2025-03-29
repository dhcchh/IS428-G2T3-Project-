import pandas as pd
import numpy as np
import dash
from dash import dcc, html, Input, Output, State, callback
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import dash_bootstrap_components as dbc
from datetime import datetime

# Load and prepare data
def load_data():
    df = pd.read_csv('etf_data_for_tableau.csv')
    df['Date'] = pd.to_datetime(df['Date'])
    return df

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server  # for deployment

# Load data
df = load_data()

# Get min and max dates for the date slider
min_date = df['Date'].min().date()
max_date = df['Date'].max().date()

# ETF information for tooltips and explanations
etf_info = {
    'SPY': 'SPDR S&P 500 ETF Trust - Tracks the S&P 500 index (large-cap US stocks)',
    'BND': 'Vanguard Total Bond Market ETF - Tracks the US investment-grade bond market',
    'VTIP': 'Vanguard Short-Term Inflation-Protected Securities ETF - Tracks inflation-protected US Treasury bonds',
    'VXUS': 'Vanguard Total International Stock ETF - Tracks global stocks excluding the US'
}

# Design the layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("Long-Term Investment Dashboard", className="text-center my-4"),
            html.H5("Time in the Market Beats Timing the Market", className="text-center text-muted mb-4"),
        ], width=12)
    ]),
    
    # User Input Controls
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Investment Parameters"),
                dbc.CardBody([
                    # Date Range Slider
                    html.Label("Investment Period:"),
                    dcc.RangeSlider(
                        id='date-slider',
                        min=0,
                        max=(max_date - min_date).days,
                        step=30,  # approximately monthly steps
                        value=[0, (max_date - min_date).days],
                        marks={
                            0: {'label': str(min_date.year)},
                            365: {'label': '2016'},
                            365*2: {'label': '2017'},
                            365*3: {'label': '2018'},
                            365*4: {'label': '2019'},
                            365*5: {'label': '2020'},
                            365*6: {'label': '2021'},
                            365*7: {'label': '2022'},
                            365*8: {'label': '2023'},
                            365*9: {'label': '2024'},
                            (max_date - min_date).days: {'label': str(max_date.year)}
                        }
                    ),
                    html.Div(id='date-range-display', className="text-center my-2"),
                    
                    html.Hr(),
                    
                    # Initial Investment Input
                    html.Label("Initial Investment (USD):"),
                    dbc.Input(
                        id='initial-investment',
                        type='number',
                        min=1000,
                        max=1000000,
                        step=1000,
                        value=10000,
                        className="mb-3"
                    ),
                    html.Small("Min: $1,000 - Max: $1,000,000", className="text-muted d-block mb-3"),
                    
                    # ETF Allocation Sliders
                    html.Label("Portfolio Allocation:"),
                    html.Div([
                        html.Label(f"SPY - S&P 500 ({round(df['SPY'].iloc[-1]/df['SPY'].iloc[0] - 1, 2)*100:.1f}% total return)"),
                        dcc.Slider(
                            id='spy-allocation',
                            min=0,
                            max=100,
                            step=5,
                            value=25,
                            marks={0: '0%', 25: '25%', 50: '50%', 75: '75%', 100: '100%'},
                            tooltip={"placement": "bottom", "always_visible": True}
                        ),
                        
                        html.Label(f"BND - US Bonds ({round(df['BND'].iloc[-1]/df['BND'].iloc[0] - 1, 2)*100:.1f}% total return)"),
                        dcc.Slider(
                            id='bnd-allocation',
                            min=0,
                            max=100,
                            step=5,
                            value=25,
                            marks={0: '0%', 25: '25%', 50: '50%', 75: '75%', 100: '100%'},
                            tooltip={"placement": "bottom", "always_visible": True}
                        ),
                        
                        html.Label(f"VTIP - Inflation-Protected ({round(df['VTIP'].iloc[-1]/df['VTIP'].iloc[0] - 1, 2)*100:.1f}% total return)"),
                        dcc.Slider(
                            id='vtip-allocation',
                            min=0,
                            max=100,
                            step=5,
                            value=25,
                            marks={0: '0%', 25: '25%', 50: '50%', 75: '75%', 100: '100%'},
                            tooltip={"placement": "bottom", "always_visible": True}
                        ),
                        
                        html.Label(f"VXUS - International Stocks ({round(df['VXUS'].iloc[-1]/df['VXUS'].iloc[0] - 1, 2)*100:.1f}% total return)"),
                        dcc.Slider(
                            id='vxus-allocation',
                            min=0,
                            max=100,
                            step=5,
                            value=25,
                            marks={0: '0%', 25: '25%', 50: '50%', 75: '75%', 100: '100%'},
                            tooltip={"placement": "bottom", "always_visible": True}
                        ),
                    ]),
                    
                    html.Div(id='allocation-warning', className="text-danger mt-2"),
                    
                    html.Hr(),
                    
                    # Calculate Button
                    dbc.Button("Calculate Returns", id="calculate-button", color="primary", className="w-100"),
                ])
            ], className="mb-4"),
        ], width=12, md=3),
        
        # Results and Charts
        dbc.Col([
            # Key Metrics Cards
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Final Portfolio Value"),
                        dbc.CardBody([
                            html.H3(id="final-value", className="text-center"),
                            html.P(id="initial-value", className="text-muted text-center mb-0")
                        ])
                    ])
                ], width=6, md=3),
                
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Total Return"),
                        dbc.CardBody([
                            html.H3(id="total-return", className="text-center"),
                            html.P(id="annualized-return", className="text-muted text-center mb-0")
                        ])
                    ])
                ], width=6, md=3),
                
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Maximum Drawdown"),
                        dbc.CardBody([
                            html.H3(id="max-drawdown", className="text-center"),
                            html.P("Largest decline from peak", className="text-muted text-center mb-0")
                        ])
                    ])
                ], width=6, md=3),
                
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Risk Level"),
                        dbc.CardBody([
                            html.H3(id="volatility", className="text-center"),
                            html.P("Portfolio volatility", className="text-muted text-center mb-0")
                        ])
                    ])
                ], width=6, md=3),
            ], className="mb-4"),
            
                # Charts
            dbc.Tabs([
                dbc.Tab([
                    dcc.Graph(id='portfolio-growth-chart', style={'height': '500px'}),
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("Understanding Portfolio Growth", className="card-title"),
                            html.P([
                                "This chart shows how your investment would have grown over time. ",
                                "The y-axis represents the total dollar value of your portfolio, while the x-axis shows the date. ",
                                "The colored areas represent the contribution of each ETF to your total portfolio value."
                            ]),
                            html.P([
                                html.Strong("Key Insights:"), 
                                " The steeper the line, the faster your money is growing. Flat or downward slopes represent periods of stagnation or loss. ",
                                "The power of compounding becomes more apparent the longer you stay invested."
                            ])
                        ])
                    ], className="mt-3 mb-4")
                ], label="Portfolio Growth"),
                
                dbc.Tab([
                    dcc.Graph(id='drawdown-chart', style={'height': '500px'}),
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("Understanding Drawdowns", className="card-title"),
                            html.P([
                                "This chart shows the percentage decline from previous peak values. ",
                                "Drawdowns represent temporary losses that test your emotional resilience as an investor. ",
                                "A drawdown of -20% means your portfolio temporarily lost 20% of its value from its previous high point."
                            ]),
                            html.P([
                                html.Strong("Key Insights:"), 
                                " Larger drawdowns indicate higher risk. Risk-averse investors should pay close attention to maximum drawdowns ",
                                "to ensure they can emotionally tolerate these temporary losses without selling in panic."
                            ])
                        ])
                    ], className="mt-3 mb-4")
                ], label="Drawdown Analysis"),
                
                dbc.Tab([
                    dcc.Graph(id='etf-comparison-chart', style={'height': '500px'}),
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("Understanding ETF Comparison", className="card-title"),
                            html.P([
                                "This chart compares the performance of each ETF normalized to the same starting point. ",
                                "The y-axis shows percentage return since the starting date, making it easy to compare ETFs regardless of their price. "
                            ]),
                            html.P([
                                html.Strong("Key Insights:"), 
                                " More volatile ETFs (like SPY and VXUS) typically show larger swings both up and down. ",
                                "Less volatile ETFs (like BND and VTIP) show more stable but typically lower returns. ",
                                "Diversification works because different ETFs often perform differently at the same time."
                            ])
                        ])
                    ], className="mt-3 mb-4")
                ], label="ETF Comparison"),
                
                dbc.Tab([
                    dcc.Graph(id='yearly-returns-chart', style={'height': '500px'}),
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("Understanding Yearly Returns", className="card-title"),
                            html.P([
                                "This chart shows the performance of your portfolio in each calendar year. ",
                                "Green bars represent positive returns (gains), while red bars represent negative returns (losses). ",
                                "The percentage shown is the total return for that specific year."
                            ]),
                            html.P([
                                html.Strong("Key Insights:"), 
                                " Year-to-year returns can vary significantly, highlighting why short-term performance shouldn't drive long-term decisions. ",
                                "Even well-diversified portfolios experience negative years. ",
                                "The long-term trend matters more than any single year's performance."
                            ])
                        ])
                    ], className="mt-3 mb-4")
                ], label="Yearly Returns"),
            ]),
        ], width=12, md=9)
    ]),
    
    dbc.Row([
        dbc.Col([
            html.Hr(),
            html.Div([
                html.H5("Notes for Risk-Averse Long-Term Investors:"),
                html.Ul([
                    html.Li("Diversification across asset classes can help reduce risk while maintaining returns."),
                    html.Li("BND and VTIP typically have lower volatility, making them suitable for risk-averse investors."),
                    html.Li("Time in the market is more important than timing the market for long-term investors."),
                    html.Li("Regular rebalancing helps maintain your desired risk level over time."),
                    html.Li("The historical maximum drawdown gives you an idea of how much your portfolio might decline in stressed market conditions.")
                ]),
                html.P("Data source: Historical ETF prices from 2015-2025. Past performance is not indicative of future results.")
            ], className="mb-4"),
        ], width=12)
    ])
], fluid=True)

# Helper functions for calculations
def calculate_portfolio_value(df, start_date, end_date, initial_investment, allocations):
    """Calculate portfolio value based on allocations and investment amount"""
    # Filter data by date range
    mask = (df['Date'] >= start_date) & (df['Date'] <= end_date)
    period_df = df.loc[mask].copy()
    
    if len(period_df) == 0:
        return pd.DataFrame()  # Return empty if no data in range
    
    # Normalize ETF prices to the first date
    first_date = period_df['Date'].iloc[0]
    first_prices = {}
    for etf in ['SPY', 'BND', 'VTIP', 'VXUS']:
        first_prices[etf] = period_df.loc[period_df['Date'] == first_date, etf].values[0]
    
    # Calculate values based on allocations
    total_allocation = sum(allocations.values())
    if total_allocation != 0:  # Avoid division by zero
        scale_factor = 100 / total_allocation
        for etf in allocations:
            allocations[etf] = allocations[etf] * scale_factor
    
    # Calculate ETF values over time
    for etf in ['SPY', 'BND', 'VTIP', 'VXUS']:
        # Skip if allocation is 0
        if allocations[etf] == 0:
            period_df[f'{etf}_value'] = 0
            continue
            
        # Calculate normalized return
        period_df[f'{etf}_norm'] = period_df[etf] / first_prices[etf]
        
        # Calculate value based on allocation
        etf_investment = initial_investment * (allocations[etf] / 100)
        period_df[f'{etf}_value'] = etf_investment * period_df[f'{etf}_norm']
    
    # Calculate total portfolio value
    period_df['total_value'] = period_df['SPY_value'] + period_df['BND_value'] + period_df['VTIP_value'] + period_df['VXUS_value']
    
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
    days = (portfolio_df['Date'].iloc[-1] - portfolio_df['Date'].iloc[0]).days
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
        'initial_value': initial_value,
        'final_value': final_value,
        'total_return': total_return,
        'annualized_return': annualized_return,
        'max_drawdown': max_drawdown,
        'volatility': annualized_volatility,
        'risk_level': risk_level,
        'sharpe_ratio': sharpe_ratio,
        'years': years
    }

# Callbacks
@callback(
    Output('date-range-display', 'children'),
    Input('date-slider', 'value')
)
def update_date_range_text(date_range):
    start_date = min_date + pd.Timedelta(days=date_range[0])
    end_date = min_date + pd.Timedelta(days=date_range[1])
    return f"From {start_date.strftime('%b %Y')} to {end_date.strftime('%b %Y')}"

@callback(
    Output('allocation-warning', 'children'),
    [
        Input('spy-allocation', 'value'),
        Input('bnd-allocation', 'value'),
        Input('vtip-allocation', 'value'),
        Input('vxus-allocation', 'value')
    ]
)
def check_allocation(spy, bnd, vtip, vxus):
    total = spy + bnd + vtip + vxus
    if total != 100:
        return f"Total allocation: {total}% (should be 100%)"
    return ""

@callback(
    [
        Output('final-value', 'children'),
        Output('initial-value', 'children'),
        Output('total-return', 'children'),
        Output('annualized-return', 'children'),
        Output('max-drawdown', 'children'),
        Output('volatility', 'children'),
        Output('portfolio-growth-chart', 'figure'),
        Output('drawdown-chart', 'figure'),
        Output('etf-comparison-chart', 'figure'),
        Output('yearly-returns-chart', 'figure')
    ],
    Input('calculate-button', 'n_clicks'),
    [
        State('date-slider', 'value'),
        State('initial-investment', 'value'),
        State('spy-allocation', 'value'),
        State('bnd-allocation', 'value'),
        State('vtip-allocation', 'value'),
        State('vxus-allocation', 'value')
    ]
)
def update_results(n_clicks, date_range, initial_investment, spy_alloc, bnd_alloc, vtip_alloc, vxus_alloc):
    # Convert slider values to dates
    start_date = min_date + pd.Timedelta(days=date_range[0])
    end_date = min_date + pd.Timedelta(days=date_range[1])
    
    # Calculate portfolio values
    allocations = {
        'SPY': spy_alloc,
        'BND': bnd_alloc,
        'VTIP': vtip_alloc,
        'VXUS': vxus_alloc
    }
    
    portfolio_df, yearly_returns = calculate_portfolio_value(
        df, 
        pd.Timestamp(start_date), 
        pd.Timestamp(end_date), 
        initial_investment, 
        allocations
    )
    
    # If no data, return empty results
    if len(portfolio_df) == 0:
        empty_fig = go.Figure()
        empty_fig.update_layout(title="No data available for selected date range")
        return (
            "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", 
            empty_fig, empty_fig, empty_fig, empty_fig
        )
    
    # Calculate metrics
    metrics = calculate_risk_metrics(portfolio_df)
    
    # Create portfolio growth chart
    growth_fig = go.Figure()
    
    # Add total portfolio value with formatted hover data
    growth_fig.add_trace(
        go.Scatter(
            x=portfolio_df['Date'],
            y=portfolio_df['total_value'],
            mode='lines',
            name='Total Portfolio Value',
            line=dict(color='rgb(0, 100, 80)', width=2),
            hovertemplate='Date: %{x|%b %d, %Y}<br>Value: $%{y:.2f}<extra></extra>'
        )
    )
    
    # Add contribution from each ETF
    colors = {
        'SPY': 'rgba(0, 150, 136, 0.7)',
        'BND': 'rgba(63, 81, 181, 0.7)',
        'VTIP': 'rgba(255, 152, 0, 0.7)',
        'VXUS': 'rgba(233, 30, 99, 0.7)'
    }
    
    # Add a filled area chart for each ETF with formatted hover data
    for etf in ['SPY', 'BND', 'VTIP', 'VXUS']:
        if allocations[etf] > 0:
            growth_fig.add_trace(
                go.Scatter(
                    x=portfolio_df['Date'],
                    y=portfolio_df[f'{etf}_value'],
                    mode='lines',
                    name=f'{etf} Value',
                    stackgroup='one',
                    line=dict(width=0.5),
                    fillcolor=colors[etf],
                    hovertemplate='Date: %{x|%b %d, %Y}<br>' + f'{etf}: $%{{y:.2f}}<extra></extra>'
                )
            )
    
    growth_fig.update_layout(
        title='Portfolio Growth Over Time',
        xaxis_title='Date',
        yaxis_title='Value (USD)',
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Create drawdown chart
    drawdown_fig = go.Figure()
    
    drawdown_fig.add_trace(
        go.Scatter(
            x=portfolio_df['Date'],
            y=portfolio_df['drawdown'] * 100,
            mode='lines',
            name='Drawdown',
            line=dict(color='rgb(255, 0, 0)', width=2),
            fill='tozeroy',
            fillcolor='rgba(255, 0, 0, 0.3)',
            hovertemplate='Date: %{x|%b %d, %Y}<br>Drawdown: %{y:.2f}%<extra></extra>'
        )
    )
    
    drawdown_fig.update_layout(
        title='Portfolio Drawdown Analysis',
        xaxis_title='Date',
        yaxis_title='Drawdown (%)',
        yaxis=dict(tickformat='.1f', ticksuffix='%'),
        hovermode='x unified'
    )
    
    # Create ETF comparison chart
    comparison_fig = go.Figure()
    
    # Normalize ETF prices to initial date for fair comparison
    for etf in ['SPY', 'BND', 'VTIP', 'VXUS']:
        if etf in portfolio_df.columns:
            initial_price = portfolio_df[etf].iloc[0]
            if initial_price > 0:
                normalized_values = (portfolio_df[etf] / initial_price - 1) * 100
                comparison_fig.add_trace(
                    go.Scatter(
                        x=portfolio_df['Date'],
                        y=normalized_values,
                        mode='lines',
                        name=f'{etf}',
                        line=dict(width=2),
                        hovertemplate='Date: %{x|%b %d, %Y}<br>' + f'{etf} Return: %{{y:.2f}}%<extra></extra>'
                    )
                )
    
    comparison_fig.update_layout(
        title='ETF Performance Comparison',
        xaxis_title='Date',
        yaxis_title='Return (%)',
        yaxis=dict(tickformat='.1f', ticksuffix='%'),
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Create yearly returns chart
    yearly_fig = go.Figure()
    
    yearly_fig.add_trace(
        go.Bar(
            x=yearly_returns['year'],
            y=yearly_returns['yearly_return'] * 100,
            marker_color=['rgb(0, 153, 76)' if r >= 0 else 'rgb(204, 0, 0)' for r in yearly_returns['yearly_return']],
            text=[f"{r*100:.1f}%" for r in yearly_returns['yearly_return']],
            textposition='outside',
            hovertemplate='Year: %{x}<br>Return: %{y:.2f}%<extra></extra>'
        )
    )
    
    yearly_fig.update_layout(
        title='Yearly Portfolio Returns',
        xaxis_title='Year',
        yaxis_title='Return (%)',
        yaxis=dict(tickformat='.1f', ticksuffix='%'),
        hovermode='x unified'
    )
    
    # Format output values
    final_value_formatted = f"${metrics['final_value']:,.2f}"
    initial_value_formatted = f"Initial: ${metrics['initial_value']:,.2f}"
    total_return_formatted = f"{metrics['total_return']*100:.1f}%"
    annualized_return_formatted = f"Annualized: {metrics['annualized_return']*100:.1f}% per year"
    max_drawdown_formatted = f"{metrics['max_drawdown']*100:.1f}%"
    volatility_formatted = f"{metrics['risk_level']} ({metrics['volatility']*100:.1f}%)"
    
    return (
        final_value_formatted,
        initial_value_formatted,
        total_return_formatted,
        annualized_return_formatted,
        max_drawdown_formatted,
        volatility_formatted,
        growth_fig,
        drawdown_fig,
        comparison_fig,
        yearly_fig
    )

if __name__ == '__main__':
    app.run_server(debug=True)