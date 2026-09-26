"""
NIFTY 50 companies (Yahoo Finance symbols end with .NS).

List as of the NSE rejig effective 30 September 2026
(BSE Ltd added, Wipro Ltd removed).
NSE reviews the index every March and September —
when it changes, just edit this list. No database changes needed.
"""

NIFTY50_INDEX = {"symbol": "^NSEI", "name": "NIFTY 50 Index", "sector": "Index"}

NIFTY50 = [
    {"symbol": "ADANIENT.NS", "name": "Adani Enterprises", "sector": "Metals & Mining"},
    {"symbol": "ADANIPORTS.NS", "name": "Adani Ports & SEZ", "sector": "Services"},
    {"symbol": "APOLLOHOSP.NS", "name": "Apollo Hospitals", "sector": "Healthcare"},
    {"symbol": "ASIANPAINT.NS", "name": "Asian Paints", "sector": "Consumer Durables"},
    {"symbol": "AXISBANK.NS", "name": "Axis Bank", "sector": "Financial Services"},
    {"symbol": "BAJAJ-AUTO.NS", "name": "Bajaj Auto", "sector": "Automobile"},
    {"symbol": "BAJFINANCE.NS", "name": "Bajaj Finance", "sector": "Financial Services"},
    {"symbol": "BAJAJFINSV.NS", "name": "Bajaj Finserv", "sector": "Financial Services"},
    {"symbol": "BEL.NS", "name": "Bharat Electronics", "sector": "Capital Goods"},
    {"symbol": "BHARTIARTL.NS", "name": "Bharti Airtel", "sector": "Telecom"},
    {"symbol": "BSE.NS", "name": "BSE Ltd", "sector": "Financial Services"},
    {"symbol": "CIPLA.NS", "name": "Cipla", "sector": "Healthcare"},
    {"symbol": "COALINDIA.NS", "name": "Coal India", "sector": "Oil, Gas & Fuels"},
    {"symbol": "DRREDDY.NS", "name": "Dr. Reddy's Laboratories", "sector": "Healthcare"},
    {"symbol": "EICHERMOT.NS", "name": "Eicher Motors", "sector": "Automobile"},
    {"symbol": "ETERNAL.NS", "name": "Eternal (Zomato)", "sector": "Consumer Services"},
    {"symbol": "GRASIM.NS", "name": "Grasim Industries", "sector": "Construction Materials"},
    {"symbol": "HCLTECH.NS", "name": "HCLTech", "sector": "Information Technology"},
    {"symbol": "HDFCBANK.NS", "name": "HDFC Bank", "sector": "Financial Services"},
    {"symbol": "HDFCLIFE.NS", "name": "HDFC Life", "sector": "Financial Services"},
    {"symbol": "HINDALCO.NS", "name": "Hindalco Industries", "sector": "Metals & Mining"},
    {"symbol": "HINDUNILVR.NS", "name": "Hindustan Unilever", "sector": "FMCG"},
    {"symbol": "ICICIBANK.NS", "name": "ICICI Bank", "sector": "Financial Services"},
    {"symbol": "INDIGO.NS", "name": "InterGlobe Aviation (IndiGo)", "sector": "Services"},
    {"symbol": "INFY.NS", "name": "Infosys", "sector": "Information Technology"},
    {"symbol": "ITC.NS", "name": "ITC", "sector": "FMCG"},
    {"symbol": "JIOFIN.NS", "name": "Jio Financial Services", "sector": "Financial Services"},
    {"symbol": "JSWSTEEL.NS", "name": "JSW Steel", "sector": "Metals & Mining"},
    {"symbol": "KOTAKBANK.NS", "name": "Kotak Mahindra Bank", "sector": "Financial Services"},
    {"symbol": "LT.NS", "name": "Larsen & Toubro", "sector": "Construction"},
    {"symbol": "M&M.NS", "name": "Mahindra & Mahindra", "sector": "Automobile"},
    {"symbol": "MARUTI.NS", "name": "Maruti Suzuki", "sector": "Automobile"},
    {"symbol": "MAXHEALTH.NS", "name": "Max Healthcare", "sector": "Healthcare"},
    {"symbol": "NESTLEIND.NS", "name": "Nestlé India", "sector": "FMCG"},
    {"symbol": "NTPC.NS", "name": "NTPC", "sector": "Power"},
    {"symbol": "ONGC.NS", "name": "Oil & Natural Gas Corp", "sector": "Oil, Gas & Fuels"},
    {"symbol": "POWERGRID.NS", "name": "Power Grid Corp", "sector": "Power"},
    {"symbol": "RELIANCE.NS", "name": "Reliance Industries", "sector": "Oil, Gas & Fuels"},
    {"symbol": "SBILIFE.NS", "name": "SBI Life Insurance", "sector": "Financial Services"},
    {"symbol": "SBIN.NS", "name": "State Bank of India", "sector": "Financial Services"},
    {"symbol": "SHRIRAMFIN.NS", "name": "Shriram Finance", "sector": "Financial Services"},
    {"symbol": "SUNPHARMA.NS", "name": "Sun Pharma", "sector": "Healthcare"},
    {"symbol": "TATACONSUM.NS", "name": "Tata Consumer Products", "sector": "FMCG"},
    {"symbol": "TATASTEEL.NS", "name": "Tata Steel", "sector": "Metals & Mining"},
    {"symbol": "TCS.NS", "name": "Tata Consultancy Services", "sector": "Information Technology"},
    {"symbol": "TECHM.NS", "name": "Tech Mahindra", "sector": "Information Technology"},
    {"symbol": "TITAN.NS", "name": "Titan Company", "sector": "Consumer Durables"},
    {"symbol": "TMPV.NS", "name": "Tata Motors Passenger Vehicles", "sector": "Automobile"},
    {"symbol": "TRENT.NS", "name": "Trent", "sector": "Consumer Services"},
    {"symbol": "ULTRACEMCO.NS", "name": "UltraTech Cement", "sector": "Construction Materials"},
]

NIFTY50_BY_SYMBOL = {c["symbol"]: c for c in NIFTY50}
NIFTY50_BY_SYMBOL[NIFTY50_INDEX["symbol"]] = NIFTY50_INDEX


def sectors():
    """Sorted list of (sector, number of companies)."""
    counts = {}
    for c in NIFTY50:
        counts[c["sector"]] = counts.get(c["sector"], 0) + 1
    return sorted(counts.items(), key=lambda x: (-x[1], x[0]))
