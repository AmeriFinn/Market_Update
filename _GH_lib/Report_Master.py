# -*- coding: utf-8 -*-
"""
Created on Fri Feb 11 21:16:53 2022

@author: grega
"""
import time

import EquityAnalysis as EA
from mwr_utils import my_str_to_date, EndOfWeek
from yield_plot import yield_curve
import my_weekly_articles as mwa
from dp_post import DataPane_Post
from figure_frames import HPR_df

## Import selenium for web scraping
from selenium import webdriver
from init_browser import init_browser
# from selenium.webdriver.common.by import By
# from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException

# Create datetime variables for monday and friday of this week
monday = my_str_to_date(EndOfWeek(True)[0])
friday = my_str_to_date(EndOfWeek(True)[1])

## Collect the necessary price/yield info
Tickers = [
    '^GSPC', '^DJI', '^IXIC', 'VTI', 'VEU', 'VDE', '^VIX', 'GC=F',
    'CL=F', 'ZC=F', 'EURUSD=X', 'GBPUSD=X', 'CNYUSD=X', 'BTC-USD'
]
AsstCls = ['EQUITY' for tick in Tickers]

names   = {
    '^GSPC': 'S&P 500 Index',
    '^DJI': 'Dow Jones Industrial Average',
    '^IXIC': 'NASDAQ Composite Index',
    'VTI': 'Vanguard Total U.S. Stock Market Index Fund',
    'VEU': 'Vanguard All-World ex-U.S. Large Blend ETF',
    'VDE': 'Vanguard Energy Index Fund ETF',
    '^VIX': 'S&P 500 Volatility Index',
    'GC=F': 'Gold Front Month Futures',
    'CL=F': 'Crude Oil WTI Front Month Futures',
    'ZC=F': 'Corn Front Month Futures',
    'EURUSD=X': 'EURO-USD',
    'GBPUSD=X': 'GBP-USD',
    'CNYUSD=X': 'CNY-USD',
    'BTC-USD': 'Bitcoin-USD'
}
data = EA.Data(tickers = Tickers,
                period='3y',
                interval='1d')
data.Collect(DataType='prices')
all_prices = data.PriceData

stats_df, decile_data = HPR_df(all_prices, '^GSPC', friday)
# stats_df

# Yield Curve
yc_dat = yield_curve(friday)

# Create the necessary webdriver object
driver = init_browser()

# Collect relevant article links using the `my_weekly_articles.py` script
article_dfs_lst = []
keys = []
i = 1
for asset_class, tick in zip(AsstCls + ['EQUITY'], Tickers + ['YIELD']):
    
    print(f"Collecting articles for {tick}\n\n")
    
    if tick not in keys:
        
        sa = mwa.summarize_articles(asset_class, tick, driver = driver)
        sa.go()
        
        index_df = sa.index_df
        index_df = index_df.loc[
            :10,
            ['LMcD_Neg_Terms',  'LMcD_Pos_Terms',  'LMcD_Tot_Terms',
             'Date_Relevance',  'Title_Relevance', 'Relevancy_Score',
             'Source', 'Date', 'Title', 'Link', 'Polarity', 'Subjectivity']
        ]
        
        ## Create column for plotly/html formatted title-link combo
        index_df.loc[:, 'Article'] = index_df.apply(
            lambda x: f'<a href="{x.Link}">{x.Title}</a>',
            axis=1
        )
        
        ## Collect the asset summary
        asset_summary = sa.asset_summary
        
        article_dfs_lst.append([tick, index_df, asset_summary])
        
        i += 1
        
    print(f"Collected articles for {tick} | {round(100 * i / (len(Tickers) + 1), 2)}\n\n")
    keys.append(tick)

driver.quit()

desc = open('Authors Notes.txt').read()

DataPane_Post(Tickers, names, all_prices, yc_dat, article_dfs_lst, desc, friday)

# plotly_article_table('YIELD', article_dfs_lst)

# # # ## Test the Equity_Plot function
# e_fig = Equity_Plot(all_prices, 'BTC-USD', article_dfs_lst, names)

# # # ## Test the Yield_Plot function
# y_fig = Yield_Plot(yc_dat, article_dfs_lst)

# from plotly.offline import download_plotlyjs, init_notebook_mode,  plot
# plot(e_fig)
# plot(y_fig)
