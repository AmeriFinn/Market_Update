# -*- coding: utf-8 -*-
"""
Useful functions used across various modules of the Weekly_Market_Report library.

Created on Thu Feb 10 18:38:04 2022

@author: grega
"""

## Import the necessary modules
import datetime as dt

def lst_unique(lst: list) -> list:
    """Create a list of unique items in the passed list."""
    unique = []
    for elem in lst:
        if elem not in unique:
            unique.append(elem)
    return unique
    
def my_str_to_date(string: str) -> str:
    """Convert a formatted datetime string to a datetime class object."""
    return dt.datetime.strptime(string, "%a %d-%m-%y").date()
    
def my_date_to_str(date: dt.date, title_format: list = [False, False]) -> str:
    """
    Covert a datetime class object to a formatted string.
    
    Parameters
    ----------
    date : dt.date
        The datetime object for the desired date to be converted to a string.
        
    title_format : list, optional
        A list of boolean values determined what format should be used for the string.
        The default is [False, False].
    
    Returns
    -------
    str
        The formatted datetime string.
    
    """
    if title_format[0]:
        if title_format[1]:
            return dt.datetime.strftime(date, "%a %d-%b-%y (Week: %U)")
        else:
            return dt.datetime.strftime(date, "%a %d-%b-%y")
            
    else:
        return dt.datetime.strftime(date, "%a %d-%b-%y")
    
def EndOfWeek(include_monday: bool = False) -> list:
    """
    Determine the date of Friday in current week and return date as formatted string.
    
    If desired the date of Monday can also be determined.
    
    Parameters
    ----------
    include_monday : bool, optional
        If true, determine the date of monday and friday.
        The default is False.
        
    Returns
    -------
    list
        A list of formatted string dates.
        
    """
    today = dt.date.today()
    wkday = today.weekday()

    days_til = 4 - wkday
    end      = (today + dt.timedelta(days=days_til)).strftime("%a %d-%m-%y")
    # # dt.date(today.year, today.month, today.day + days_til)

    if include_monday:
        start    = (today + dt.timedelta(days=-wkday)).strftime("%a %d-%m-%y")
        return [start, end]
    else:
        return [end]
    
def FirstTradingDay(year=dt.date.today().year):
    """Determine the fisrt trading day of the year to be used in YTD calculations."""
    day1 = dt.date(year, 1, 2)  # Start at day 2 since no trading on Jan 1
    
    # Use While Loop to make sure first day is not a weekend
    while day1.weekday() > 4:
        day1 += dt.timedelta(days=1)
    
    return day1

def my_topic(tick):
    """Define a dictionary of asset names to be searched for in google news based on a ticker."""
    topics = {
        '^GSPC': 'S&P 500 US Markets',
        '^DJI': 'Dow Jones Industrial Average',
        '^IXIC': 'NASDAQ',
        'VTI': 'US Total Stock Market',          # 'Vanguard VTI',
        'VEU': 'Global Markets',                 # 'Vanguard VEU Global Markets',
        'VDE': 'Energy Markets',                 # 'Vanguard VDE Energy Markets',
        '^VIX': 'Market Volatility VIX',
        'GC=F': 'Gold Futures',
        'CL=F': 'Crude Oil Futures',
        'ZC=F': 'Corn Futures',
        'EURUSD=X': 'EUR-USD EuroZone European Markets',
        'GBPUSD=X': 'GBP-USD Brexit London Markets',
        'CNYUSD=X': 'CNY-USD China Markets',
        'BTC-USD': 'Bitcoin',
        'YIELD': 'US Yield Curve'
    }
    
    return topics[tick]
