import pandas as pd
import re

def clean_company_name(name):
    """Clean and standardize company names for better matching."""
    # Replace '+' with '&' or space
    name = name.replace(' + ', ' & ')
    name = name.replace('+', ' ')
    
    # Remove common suffixes
    name = re.sub(r'\bINC\b|\bCORP\b|\bCO\b|\bLTD\b|\bPLC\b|\bCLASS [A-Z]\b|\bCL [A-Z]\b|\bSHS\b|\bHOLDINGS\b|\bGROUP\b|\bTHE\b', '', name, flags=re.IGNORECASE)
    
    # Remove special characters and standardize spacing
    name = re.sub(r'[^\w\s&]', ' ', name)
    name = re.sub(r'\s+', ' ', name).strip()
    
    return name.upper()

# Sector mappings - key company keywords mapped to sectors
sector_map = {
    # Information Technology
    "APPLE": "Information Technology",
    "MICROSOFT": "Information Technology",
    "NVIDIA": "Information Technology",
    "BROADCOM": "Information Technology",
    "ADOBE": "Information Technology",
    "CISCO": "Information Technology",
    "SALESFORCE": "Information Technology",
    "INTEL": "Information Technology",
    "IBM": "Information Technology",
    "ORACLE": "Information Technology",
    "QUALCOMM": "Information Technology",
    "AMD": "Information Technology",
    "PAYPAL": "Information Technology",
    "INTUIT": "Information Technology",
    
    # Financials
    "BERKSHIRE": "Financials",
    "JPMORGAN": "Financials",
    "VISA": "Financials",
    "MASTERCARD": "Financials",
    "BANK OF AMERICA": "Financials",
    "WELLS FARGO": "Financials",
    "CITIGROUP": "Financials",
    "GOLDMAN SACHS": "Financials",
    "MORGAN STANLEY": "Financials",
    "BLACKROCK": "Financials",
    "AMERICAN EXPRESS": "Financials",
    "S&P GLOBAL": "Financials",
    
    # Health Care
    "ELI LILLY": "Health Care",
    "UNITEDHEALTH": "Health Care",
    "JOHNSON & JOHNSON": "Health Care",
    "PFIZER": "Health Care",
    "MERCK": "Health Care",
    "ABBVIE": "Health Care",
    "THERMO FISHER": "Health Care",
    "ABBOTT": "Health Care",
    "AMGEN": "Health Care",
    "BRISTOL MYERS": "Health Care",
    
    # Consumer Discretionary
    "AMAZON": "Consumer Discretionary",
    "TESLA": "Consumer Discretionary",
    "HOME DEPOT": "Consumer Discretionary",
    "MCDONALD": "Consumer Discretionary",
    "NIKE": "Consumer Discretionary",
    "STARBUCKS": "Consumer Discretionary",
    "BOOKING": "Consumer Discretionary",
    "UBER": "Consumer Discretionary",
    
    # Communication Services
    "META": "Communication Services",
    "ALPHABET": "Communication Services",
    "GOOGLE": "Communication Services",
    "NETFLIX": "Communication Services",
    "COMCAST": "Communication Services",
    "DISNEY": "Communication Services",
    "VERIZON": "Communication Services",
    "AT&T": "Communication Services",
    "T-MOBILE": "Communication Services",
    
    # Industrials
    "GENERAL ELECTRIC": "Industrials",
    "UNION PACIFIC": "Industrials",
    "BOEING": "Industrials",
    "HONEYWELL": "Industrials",
    "CATERPILLAR": "Industrials",
    "DEERE": "Industrials",
    "LOCKHEED MARTIN": "Industrials",
    "3M": "Industrials",
    "RAYTHEON": "Industrials",
    "RTX": "Industrials",
    "UPS": "Industrials",
    "FEDEX": "Industrials",
    
    # Consumer Staples
    "PROCTER & GAMBLE": "Consumer Staples",
    "WALMART": "Consumer Staples",
    "COCA COLA": "Consumer Staples",
    "PEPSICO": "Consumer Staples",
    "COSTCO": "Consumer Staples",
    "PHILIP MORRIS": "Consumer Staples",
    "MONDELEZ": "Consumer Staples",
    
    # Energy
    "EXXON": "Energy",
    "CHEVRON": "Energy",
    "CONOCOPHILLIPS": "Energy",
    "SCHLUMBERGER": "Energy",
    "EOG RESOURCES": "Energy",
    "PIONEER": "Energy",
    "OCCIDENTAL": "Energy",
    "MARATHON": "Energy",
    "VALERO": "Energy",
    "PHILLIPS 66": "Energy",
    
    # Utilities
    "NEXTERA": "Utilities",
    "DUKE ENERGY": "Utilities",
    "SOUTHERN": "Utilities",
    "DOMINION": "Utilities",
    "AMERICAN ELECTRIC": "Utilities",
    "SEMPRA": "Utilities",
    "EXELON": "Utilities",
    
    # Real Estate
    "PROLOGIS": "Real Estate",
    "AMERICAN TOWER": "Real Estate",
    "CROWN CASTLE": "Real Estate",
    "SIMON PROPERTY": "Real Estate",
    "WELLTOWER": "Real Estate",
    "PUBLIC STORAGE": "Real Estate",
    "REALTY INCOME": "Real Estate",
    
    # Materials
    "LINDE": "Materials",
    "AIR PRODUCTS": "Materials",
    "SHERWIN WILLIAMS": "Materials",
    "FREEPORT": "Materials",
    "DOW": "Materials",
    "DUPONT": "Materials",
    "NEWMONT": "Materials",
    "NUCOR": "Materials"
}

# Special case company mapping for problematic names
special_case_map = {
    "PROCTER + GAMBLE": "Consumer Staples",
    "PROCTER GAMBLE": "Consumer Staples",
    "P G": "Consumer Staples",
    "JOHNSON + JOHNSON": "Health Care",
    "J J": "Health Care",
    "AT+T": "Communication Services",
    "AT T": "Communication Services",
    "T MOBILE": "Communication Services",
    "S+P GLOBAL": "Financials",
    "S P GLOBAL": "Financials",
    "RTX": "Industrials",  # Raytheon
    "INTL BUSINESS MACHINES": "Information Technology",
    "IBM": "Information Technology",
    "ADVANCED MICRO DEVICES": "Information Technology",
    "AMD": "Information Technology",
    "UBER TECHNOLOGIES": "Consumer Discretionary",
    "UBER": "Consumer Discretionary"
}

def find_sector(company_name):
    """Find the sector for a given company name using various matching methods."""
    # Clean the company name first
    cleaned_name = clean_company_name(company_name)
    
    # Check special case map first (for problematic company names)
    for name, sector in special_case_map.items():
        if name in cleaned_name:
            return sector
    
    # Direct match with the sector map
    if cleaned_name in sector_map:
        return sector_map[cleaned_name]
    
    # Check if any key in the sector map is found within the cleaned name
    for key, sector in sector_map.items():
        if key in cleaned_name:
            return sector
        
    # Edge cases and common abbreviations
    if "MSFT" in company_name or "MICROSOFT" in cleaned_name:
        return "Information Technology"
    elif "AAPL" in company_name or "APPLE" in cleaned_name:
        return "Information Technology"
    elif "AMZN" in company_name or "AMAZON" in cleaned_name:
        return "Consumer Discretionary"
    elif "GOOGL" in company_name or "GOOG" in company_name or "ALPHABET" in cleaned_name:
        return "Communication Services"
    elif "FB" in company_name or "META" in cleaned_name or "FACEBOOK" in cleaned_name:
        return "Communication Services"
    elif "JPM" in company_name or "JPMORGAN" in cleaned_name:
        return "Financials"
    elif "JNJ" in company_name or "JOHNSON" in cleaned_name:
        return "Health Care"
        
    # Return Unknown if no match found
    return "Unknown"

def update_sectors(df):
    """Update sectors in a dataframe."""
    # Create a copy to avoid modifying the original
    updated_df = df.copy()
    
    # Apply sector mapping
    updated_df['Sector'] = updated_df.apply(lambda row: 
                         row['Sector'] if row['Sector'] and row['Sector'] != '-' 
                         else find_sector(row['Name']), axis=1)
    
    return updated_df

def update_excel_file(input_file, output_file=None):
    """Update sector information in an Excel file."""
    # Load Excel file
    df = pd.read_excel(input_file)
    
    # Update sectors
    updated_df = update_sectors(df)
    
    # Save file if output path is provided
    if output_file:
        updated_df.to_excel(output_file, index=False)
        print(f"Updated file saved to {output_file}")
    
    # Return the updated dataframe
    return updated_df

def analyze_sectors(df):
    """Analyze sector weights in the dataframe."""
    # Calculate sector weights
    sector_weights = df.groupby('Sector')['Weight'].sum().sort_values(ascending=False)
    
    # Target weights from the image
    target_weights = {
        "Information Technology": 30.39,
        "Financials": 14.22,
        "Health Care": 11.20,
        "Consumer Discretionary": 10.11,
        "Communication Services": 9.45,
        "Industrials": 8.46,
        "Consumer Staples": 5.97,
        "Energy": 3.42,
        "Utilities": 2.52,
        "Real Estate": 2.23,
        "Materials": 2.05
    }
    
    # Create analysis dataframe
    analysis = pd.DataFrame({
        'Actual': sector_weights
    })
    
    # Add target weights
    for sector, weight in target_weights.items():
        if sector not in analysis.index:
            analysis.loc[sector, 'Actual'] = 0.0
        analysis.loc[sector, 'Target'] = weight
    
    # Calculate difference
    analysis['Difference'] = analysis['Actual'] - analysis['Target']
    
    # Sort by actual weight
    analysis = analysis.sort_values('Actual', ascending=False)
    
    return analysis