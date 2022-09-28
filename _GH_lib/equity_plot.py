# -*- coding: utf-8 -*-
"""
Created on Thu Feb 10 18:53:35 2022

@author: grega
"""
import pandas as pd
import datetime as dt
from datetime import date
from plotly.subplots import make_subplots
from mwr_utils import my_date_to_str
import plotly.graph_objects as go
import plotly.express as px
from figure_frames import HPR_df, plotly_article_table

def Equity_Plot(all_prices, tick, art_lst, names, friday):
    """
    Create two interactive visuals for equity/fi benchmarks.
    
    The first figure created will be for the daily ohlc chart.
    The second chart will be a figure frame for price quartiles, HPR Data, and relevant articles.
    
    Parameters
    ----------
    all_prices : TYPE
        DESCRIPTION.
    tick : TYPE
    
        DESCRIPTION.
    art_lst : TYPE
    
        DESCRIPTION.
    names : TYPE
    
        DESCRIPTION.
        
    Returns
    -------
    None.
    
    """
    ## Define necessary objects for creating both figures
    # Define spec dictionaries for the plotly figures
    CSdict  = {"type": "xy", 'colspan': 1, 'rowspan': 1, 'secondary_y': True}  # Candlestick plot specs
    TBdict1 = {"type": "table", 'colspan': 1, 'rowspan': 1}  # HPR table specs
    TBdict2 = {"type": "table", 'colspan': 2, 'rowspan': 1}  # Articles table specs
    BPdict  = {"type": "xy", 'colspan': 1, 'rowspan': 1}     # Price quartile boxplot specs
    
    oth_specs = [
        [BPdict, TBdict1],
        [TBdict2, None]
    ]

    # Define list of subtitles
    subtitles = [
        'Closing Price Quartiles',
        "Holding Period Return Data",
        "Relevant Articles",
    ]
    
    # Create the frame for the ohlc chart
    ohlc_fig = make_subplots(
        rows           = 1,
        cols           = 1,
        specs          = [[CSdict]],
        subplot_titles = [f"[<i>${tick}</i>] as of {str(min(date.today(), friday))}<br><em>{names[tick]}"]
    )
    
    ohlc_fig.update_layout(
        template  = 'seaborn',
        height    = 600,
        # width     = 1400,
        autosize  = True,
        hovermode = 'x',
    )

    # Create the frame for the other summary charts
    scnd_fig = make_subplots(
        rows               = 2,
        cols               = 2,
        column_widths      = [1, 1],
        row_heights        = [1, 2],
        horizontal_spacing = 0.075,
        vertical_spacing   = 0.2,
        specs              = oth_specs,
        subplot_titles     = subtitles,
    )
    
    scnd_fig.update_layout(
        template  = 'seaborn',
        height    = 600,
        # width     = 1400,
        autosize  = True,
        hovermode = 'x',
    )
    
    # Seperate out the needed prices for the desired asset
    idx = pd.IndexSlice
    prices = all_prices.loc[:, idx[['Open', 'Close', 'Adj Close', 'High', 'Low'], tick]].copy()
    prices.columns = [col[0] for col in prices.columns]
    stats_df, decile_data = HPR_df(all_prices, tick, friday)
    
    # Collect the appropiate colors for the box plots
    colors = px.colors.diverging.curl
    colors = colors[:4] + colors[-5:]
    
    # Collect the articles table
    articles = plotly_article_table(tick, art_lst)
    
    ## Add the price candlesticks to the ohlc figure
    ohlc_fig.add_trace(
        go.Ohlc(
            x     = prices.index,
            open  = prices['Open'],
            high  = prices['High'],
            low   = prices['Low'],
            close = prices['Close'],
            showlegend = False,
            name  = tick,
        ),
        row = 1,
        col = 1,
        secondary_y = False,
    )
    
    # Add the 12 day and 26 day moving averages
    ema12  = prices['Close'].ewm(span=12, adjust=False).mean().round(4).copy()
    ema26  = prices['Close'].ewm(span=26, adjust=False).mean().round(4).copy()
    macd   = round(ema12 - ema26, 4)
    signal = macd.ewm(span = 9, adjust = False).mean().round(4)
    
    for dat, name, color in zip([ema12, ema26], ['Moving Avg 12', 'Moving Avg 26'], ['rgba(0,35,102,0.5)', 'rgba(178,34,34,0.5)']):
        ohlc_fig.add_trace(
            go.Scatter(
                x          = prices.index,
                y          = dat,
                showlegend = False,
                name       = name,
                line       = dict(color = color, width = 2)
            ),
            row = 1,
            col = 1
        )
    
    # Add MACD to secondary y
    ohlc_fig.add_trace(
        go.Bar(
            x          = prices.index,
            y          = macd,
            showlegend = False,
            name       = 'MACD',
            opacity    = 0.33
        ),
        row = 1,
        col = 1,
        secondary_y = True
    )
    
    # Add the signal line to the secondary y
    ohlc_fig.add_trace(
        go.Scatter(
            x          = prices.index,
            y          = signal,
            mode       = 'lines',
            showlegend = False,
            name       = 'MACD Signal',
            opacity    = 0.33
        ),
        row = 1,
        col = 1,
        secondary_y = True
    )
    
    # Add the labels
    ohlc_fig.update_yaxes(
        showgrid = False,
        title    = "<b>MACD",
        row      = 1,
        col      = 1,
        range    = [macd.min() - 25, macd.max() * 6],
        title_standoff = 0,
        secondary_y=True
    )
    
    # Add the range selector and relevant buttons to the ohlc chart
    ohlc_fig.update_xaxes(
        range = (str(date.today() + dt.timedelta(days = -21)),
                 str(date.today() + dt.timedelta(days = 1))),
        rangeselector = dict(
                       yanchor = "bottom",
                       y = -0.1,
                       buttons = list([
                           dict(count = 1, label = "YTD", step = "year", stepmode = "todate"),
                           dict(count = 7, label = "1wk", step = "day", stepmode = "backward"),
                           dict(count = 14, label = "2wk", step = "day", stepmode = "backward"),
                           dict(count = 1, label = "1m", step = "month", stepmode = "backward"),
                           dict(count = 2, label = "2m", step = "month", stepmode = "backward"),
                           dict(count = 3, label = "3m", step = "month", stepmode = "backward"),
                           dict(count = 6, label = "6m", step = "month", stepmode = "backward"),
                           dict(count = 1, label = "1y", step = "year", stepmode = "backward"),
                           dict(count = 18, label = "1.5y", step = "month", stepmode = "backward"),
                           dict(step = "all", label = "All")
                       ]),
                       font = dict(color = 'white'),
                       bgcolor = 'black',
                       activecolor = 'green',
                   ),
        row = 1,
        col = 1
    )
    
    ## Add charts and data to the secondary plotly figure
    # Add the summary box plots for price quartiles
    for i in range(len(decile_data) - 1, -1, -1):
        scnd_fig.add_trace(
            go.Box(
                y            = decile_data[i],
                name         = stats_df.columns[i],
                showlegend   = False,
                marker_color = colors[i]
            ),
            row = 1,
            col = 1
        )
        
    # Update the subplots labels
    scnd_fig.update_xaxes(
        title = "<b>Holding Period",
        row   = 1,
        col   = 1
    )
    scnd_fig.update_yaxes(
        title = "<b>Price",
        row   = 1,
        col   = 1
    )
    
    # Add the table for HPR return data
    hpr_dat = stats_df.iloc[:4, :].copy().T
        
    hpr_dat.reset_index(inplace=True, drop=False)
    hpr_dat.rename(columns={'index': ''}, inplace=True)

    # Create a list of fill colors for the table cells
    cell_fill_color = ['dodgerblue'] + ['ivory'] * 9
    head_fill_color = ['midnightblue'] * 10

    # Create the table object to be added to the figure
    table = go.Table(header = dict(values     = list(hpr_dat.columns),
                                   font       = dict(size = 14, color = 'white'),
                                   line_color = 'darkslategray',
                                   fill_color = head_fill_color,
                                   align      = 'right'),
                     cells  = dict(values     = [hpr_dat[col] for col in hpr_dat.columns],
                                   font       = dict(size = 12.5, color = 'black'),
                                   line_color = 'darkslategray',
                                   fill_color = cell_fill_color,
                                   align      = 'right',
                                   height     = 25),
                     columnwidth = [0.7, 1.15, 1, 0.9, 0.9],
                     )
    scnd_fig.add_trace(table, row = 1, col = 2)
    
    # Add table for relevant articles
    # Create a list of fill colors for the table cells
    cell_fill_color = ['whitesmoke'] * 3
    head_fill_color = ['palegoldenrod'] * 3

    # Create the table object to be added to the figure
    table = go.Table(
        header = dict(values     = list(articles.columns),
                      font       = dict(size = 13, color = 'black'),
                      line_color = 'palegoldenrod',
                      fill_color = head_fill_color,
                      align      = 'left'),
        cells  = dict(values     = [articles[col] for col in articles.columns],
                      font       = dict(size = 11, color = 'black'),
                      line_color = 'whitesmoke',
                      fill_color = cell_fill_color,
                      align      = 'left',
                      height     = 25),
        columnwidth = [1, 1, 1.6, 0.5, 0.5],
    )
    
    scnd_fig.add_trace(table, row = 2, col = 1)
    
    return ohlc_fig, scnd_fig

## Define `Add_RangeSelector` function to add a rangeselector to the plotly figures
def Add_RangeSelector(fig):
    """
    .

    Parameters
    ----------
    fig : TYPE
        DESCRIPTION.

    Returns
    -------
    fig : TYPE
        DESCRIPTION.

    """
    ## Add range slider and adjust general plot layout elements
    fig.update_layout(
        xaxis_showticklabels=True,
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="YTD", step="year", stepmode="todate"),
                    dict(count=7, label="1wk", step="day", stepmode="backward"),
                    dict(count=14, label="2wk", step="day", stepmode="backward"),
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(count=2, label="2m", step="month", stepmode="backward"),
                    dict(count=3, label="3m", step="month", stepmode="backward"),
                    dict(count=6, label="6m", step="month", stepmode="backward"),
                    dict(count=1, label="1y", step="year", stepmode="backward"),
                    dict(count=18, label="1.5y", step="month", stepmode="backward"),
                    dict(count=2, label="2y", step="year", stepmode="backward"),
                    dict(step="all")
                ]),
                font=dict(color='black')
            ),
            rangeslider=dict(
                visible=True
            ),
        ),
    )
    return fig
