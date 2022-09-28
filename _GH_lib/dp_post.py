# -*- coding: utf-8 -*-
"""
Created on Thu Feb 10 18:43:07 2022

@author: grega
"""
import sys
import os
import datetime as dt
import pandas as pd
from equity_plot import Equity_Plot
from mwr_utils import my_topic
from yield_plot import Yield_Plot
import datapane as dp
from mwr_utils import my_date_to_str

sys.path.append('')
idx = pd.IndexSlice
dp.login(token=os.environ.get("DataPane Token"))

## Define `DataPane_Post` function to create and stitch together the interactive charts
## for each benchmark
def DataPane_Post(Tickers, Names, Price_df, Yield_df, Articles_lst, desc, friday):
    """
    Publish the visuals to DataPane as multi-page report.
    
    Parameters
    ----------
    Tickers : list
        The list of equity/commodity/fx tickers being reported on.
    Names : dict
        A dictionary with the relevant Tickers as keys and their corresponding names as values.
    Price_df : pd.DataFrame
        The full dataframe of closing prices for each asset being reported on.
    Yield_df : pd.DataFrame
        The dataframe of treasury yields used in the yield-curve plot.
    Articles_lst : list
        The list of article summaries for each asset being reported on.
        
    Yields
    ------
    None.
    
    """
    ## Create the list of figures and page titles to add to DP report
    fig_lst = list()
    tit_lst = list()
    sum_lst = list()
    prc_lst = list()
    
    # Start with equity plots
    for i, tick in enumerate(Tickers):
        # Create the equity plot figure
        ohlc_fig, scnd_fig = Equity_Plot(Price_df, tick, Articles_lst, Names, friday)
        fig_lst.append([ohlc_fig, scnd_fig])
        # Add the topic/title string
        tit_lst.append(my_topic(tick))
        # Add the summary article
        sum_lst.append(Articles_lst[i][2])
        # Add the current day's price and 1-day return
        last_price = Price_df.loc[:, idx[['PCT_Change', 'Adj Close'], tick]].copy()
        last_price.dropna(inplace = True)
        lst_date = str(last_price.iloc[-1, :].name.date()) + ' 1-Day Ret.'
        lst_prce = f"${last_price.iloc[-1, :]['Adj Close'].values[0]:,.2f}"
        pct_chng = last_price.iloc[-1, :]['PCT_Change'].values[0]
        is_upchg = True if pct_chng > 0 else False
        pct_chng = f"{pct_chng:,.2f}%"
        prc_lst.append([lst_date, lst_prce, pct_chng, is_upchg])
        
    # Add yield curve
    y_fig = Yield_Plot(Yield_df, Articles_lst, friday)
    fig_lst.append(y_fig)
    tit_lst.append(my_topic('YIELD'))
    sum_lst.append(Articles_lst[-1][2])
    prc_lst.append([])
    
    # Create list of `dp.Page` args
    page_args = []
    for figs, title, summary, big_n in zip(fig_lst, tit_lst, sum_lst, prc_lst):
        if big_n != []:
            page_args.append(
                dp.Page(
                    title=title.replace('SP', 'S&P'),
                    blocks=[
                        f"## {title.replace('SP', 'S&P')}",
                        dp.Group(
                            dp.BigNumber(
                                heading          = big_n[0],
                                value            = big_n[1],
                                change           = big_n[2],
                                is_upward_change = big_n[3]
                            ),
                            dp.HTML('<p> </p>'),
                            columns = 2
                        ),
                        '### Prices - OHLC Chart',
                        figs[0],
                        '### Summary Data & Relevant Articles',
                        figs[1],
                        '## NLG Summary of Weekly Events\n\n' + summary + '\n\n' + desc
                    ]
                )
            )
        else:
            page_args.append(
                dp.Page(
                    title=title.replace('SP', 'S&P'),
                    blocks=[
                        f"## {title.replace('SP', 'S&P')}",
                        figs,
                        '## NLG Summary of Weekly Events\n\n' + summary + '\n\n' + desc
                    ]
                )
            )
        
    report_dates = [
        my_date_to_str(friday + dt.timedelta(days=-7), [True, False]), my_date_to_str(friday, [True, True])
    ]
    report_title = "Financial Markets Update"
    report_descr = ' to '.join(report_dates)
    
    # Create the DataPane report
    dp.enable_logging()
    r = dp.Report(
        # report_title,
        # report_descr,
        page_args[0],
        page_args[1],
        page_args[2],
        page_args[3],
        page_args[4],
        page_args[5],
        page_args[6],
        page_args[7],
        page_args[8],
        page_args[9],
        page_args[10],
        page_args[11],
        page_args[12],
        page_args[13],
        page_args[14],
    )
    
    r.upload(
        name        = report_title,
        open        = True,
        description = report_descr,
        publicly_visible = True,
        formatting  = dp.ReportFormatting(width=dp.ReportWidth.FULL)
    )
