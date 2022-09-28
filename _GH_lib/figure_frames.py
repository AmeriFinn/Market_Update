# -*- coding: utf-8 -*-
"""
Created on Thu Feb 10 18:40:12 2022

@author: grega
"""

import re
import datetime as dt
import pandas as pd
from mwr_utils import my_date_to_str, EndOfWeek, FirstTradingDay

def plotly_article_table(tick, art_lst):
    """
    Create a dataframe to be used for displaying the indexed articles in the datapane report.

    Parameters
    ----------
    tick : str
        The ticker of the asset topic that the article index/df will be made for.
    art_lst : lst
        A list of nested lists. The first value in the nest is the ticker, and the second value
        is the full article index.

    Returns
    -------
    pd.DataFrame
        The refined pandas df of the article index.

    """
    # Collect the appropiate df and columns
    for i in art_lst:
        if i[0] == tick:
            df = i[1][['Source', 'Date', 'Article', 'Polarity', 'Subjectivity']]
    
    # Clean up the Source and Date columns
    def clean_source(source):
        source = re.sub('seeking_alpha', 'Seeking Alpha', source)
        source = re.sub('MarketWatch', 'Market Watch', source)
        source = re.sub('Associated', 'Assoc.', source)
        source = re.sub('New York Times', 'NYT', source)
        source = re.sub('Wall Street Journal', 'WSJ', source)
        source = re.sub('Marketscreener', 'Market Screener', source)
        source = re.sub('.com|The', '', source)
        source = source.strip()
        
        return source
    df.loc[:, 'Source'] = df.Source.apply(lambda x: f"<b>{clean_source(x)}</b>")
    df.loc[:, 'Date']   = df.Date.apply(lambda x: my_date_to_str(x, [True, False]))
    df.loc[:, 'Polarity']   = df.Polarity.apply(lambda x: f'{x}%')
    df.loc[:, 'Subjectivity']   = df.Subjectivity.apply(lambda x: f'{x}%')
    return df

## Define `HPR_df` to create a summary table of return data
def HPR_df(df, tick, friday):
    """
    Calculate the holding period return data for the desired asset.

    Parameters
    ----------
    df : pd.DataFrame
        The price df of the given asset collected from yahoo finance.
    
    tick : str
        The asset ticker.

    Returns
    -------
    hpr_df : pd.DataFrame
        The holding period returns data.
        
    quartile_data : TYPE
        The closing price quartile data used in the closing quartiles chart.

    """
    # Define a storage dictionary
    stats_dict = {}
    for key in ['1wk', '2wk', '1mo', '3mo', '6mo', '1y', '1.5y', '2y']:
        stats_dict[key] = []
    
    # Subset out the Closing prices
    idx = pd.IndexSlice
    df = df.loc[:, idx[['Close', 'PCT_Change'], tick]]
    df.columns = ['Close', '1 Day Change']
    
    # Calculate the return for this week (based on close of last week)
    quartiles = [0, 0.25, 0.5, 0.75, 1]
    quartile_data = []
    
    # Start with YTD stats
    temp_df = df.loc[(df.index.date >= FirstTradingDay()) & (df.index.date <= friday), :]
    quartile_data.append(list(temp_df.Close))

    ret = round(100 * (temp_df.Close.iloc[-1] / temp_df.Close.iloc[0] - 1), 2)
    chg = round(temp_df.Close.iloc[-1] - temp_df.Close.iloc[0], 2)
    
    ## Error handling for when yfinance data doesn't provide enough price data,
    ## or the script is being run prior to the end of the week
    if str(ret) == 'nan':

        if (str(temp_df.Close.iloc[0]) != 'nan') & (str(temp_df.Close.iloc[-1]) == 'nan'):
            ret = round(100 * (temp_df.Close.iloc[-2] / temp_df.Close.iloc[0] - 1), 2)
            chg = round(temp_df.Close.iloc[-2] - temp_df.Close.iloc[0], 2)

        elif (str(temp_df.Close.iloc[0]) == 'nan') & (str(temp_df.Close.iloc[-1]) != 'nan'):
            ret = round(100 * (temp_df.Close.iloc[-1] / temp_df.Close.iloc[1] - 1), 2)
            chg = round(temp_df.Close.iloc[-1] - temp_df.Close.iloc[1], 2)

        elif (str(temp_df.Close.iloc[0]) == 'nan') & (str(temp_df.Close.iloc[-1]) == 'nan'):
            ret = round(100 * (temp_df.Close.iloc[-2] / temp_df.Close.iloc[1] - 1), 2)
            chg = round(temp_df.Close.iloc[-2] - temp_df.Close.iloc[1], 2)

            i = 0
            while str(ret) == 'nan':
                i += 1
                ret = round(100 * (temp_df.Close.iloc[-1 - i] / temp_df.Close.iloc[0 + i] - 1), 2)
                chg = round(temp_df.Close.iloc[-1 - i] - temp_df.Close.iloc[0 + i], 2)

    mu  = round(temp_df['1 Day Change'].mean(), 2)
    sd  = round(temp_df['1 Day Change'].std(), 2)
    sum_stats = [chg, ret, mu, sd]

    qnt_stats = [round(temp_df.Close.quantile(dec), 2) for dec in quartiles]
    stats_dict['YTD'] = sum_stats + qnt_stats
    
    list_keys = list(stats_dict.keys())
    list_date_range = [7, 7 * 2, 7 * 4, 7 * 12, 7 * 24, 7 * 52, 7 * 76, 7 * 104]
    for key, day in zip(list_keys, list_date_range):
        start_friday = friday + dt.timedelta(days=-day)
        
        ## Use while loop to move `start_friday` back if its a weekend or markets were closed
        while (start_friday.weekday() > 4) | (str(df.loc[df.index.date >= start_friday, 'Close'].iloc[0]) == 'nan'):
            start_friday += dt.timedelta(days=-1)
        
        temp_df = df.loc[(df.index.date >= start_friday) & (df.index.date <= friday), :]
        quartile_data.append(list(temp_df.Close))
        
        ret = round(100 * (temp_df.Close.iloc[-1] / temp_df.Close.iloc[0] - 1), 2)
        chg = round(temp_df.Close.iloc[-1] - temp_df.Close.iloc[0], 2)
        ## Error handling for when yfinance data doesnt provide enough price data
        if str(ret) == 'nan':
            
            if (str(temp_df.Close.iloc[0]) != 'nan') & (str(temp_df.Close.iloc[-1]) == 'nan'):
                ret = round(100 * (temp_df.Close.iloc[-2] / temp_df.Close.iloc[0] - 1), 2)
                chg = round(temp_df.Close.iloc[-2] - temp_df.Close.iloc[0], 2)
                
            elif (str(temp_df.Close.iloc[0]) == 'nan') & (str(temp_df.Close.iloc[-1]) != 'nan'):
                ret = round(100 * (temp_df.Close.iloc[-1] / temp_df.Close.iloc[1] - 1), 2)
                chg = round(temp_df.Close.iloc[-1] - temp_df.Close.iloc[1], 2)
                
            elif (str(temp_df.Close.iloc[0]) == 'nan') & (str(temp_df.Close.iloc[-1]) == 'nan'):
                ret = round(100 * (temp_df.Close.iloc[-2] / temp_df.Close.iloc[1] - 1), 2)
                chg = round(temp_df.Close.iloc[-2] - temp_df.Close.iloc[1], 2)

                i = 0
                while str(ret) == 'nan':
                    i += 1
                    ret = round(100 * (temp_df.Close.iloc[-1 - i] / temp_df.Close.iloc[0 + i] - 1), 2)
                    chg = round(temp_df.Close.iloc[-1 - i] - temp_df.Close.iloc[0 + i], 2)
                        
        mu  = round(temp_df['1 Day Change'].mean(), 2)
        sd  = round(temp_df['1 Day Change'].std(), 2)
        sum_stats = [chg, ret, mu, sd]
        
        qnt_stats = [round(temp_df.Close.quantile(dec), 2) for dec in quartiles]
        stats_dict[key] = sum_stats + qnt_stats
        
    hpr_df = pd.DataFrame.from_dict(stats_dict)
    labels = ['HPR($)', 'HPR(%)', 'µ(%)', 'σ(%)', 'Min. Price'] + [f"{int(100 * i)}th PCTL" for i in quartiles[1:-1]] + ['Max. Price']
    hpr_df.index = labels
    hpr_df = hpr_df[['YTD'] + [col for col in hpr_df.columns if col != 'YTD']]
    
    return hpr_df, quartile_data
