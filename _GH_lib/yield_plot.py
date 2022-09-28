# -*- coding: utf-8 -*-
"""
Created on Thu Feb 10 18:54:31 2022

@author: grega
"""
import pandas as pd
import datetime as dt
from mwr_utils import lst_unique, my_date_to_str
from plotly.subplots import make_subplots
import plotly.express as px
import plotly.graph_objects as go
import plotly.express as px
from figure_frames import plotly_article_table

## Define `yield_curve` function for collecting US Yield Curve data
def yield_curve(friday):
    """
    Use to collect US Yield Curve data directly from US Treasury site.
    
    Parameters
    ----------
    friday : TYPE
        DESCRIPTION.
        
    Returns
    -------
    df : TYPE
        DESCRIPTION.
        
    """
    # Collect data provided by the US treasury
    y1_link = f"https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve&field_tdr_date_value={friday.year}"
    y2_link = f"https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve&field_tdr_date_value={friday.year - 1}"
    y3_link = f"https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve&field_tdr_date_value={friday.year - 2}"
    y4_link = f"https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve&field_tdr_date_value={friday.year - 3}"

    y1_df = pd.read_html(y1_link)[0]
    y2_df = pd.read_html(y2_link)[0]
    y3_df = pd.read_html(y3_link)[0]
    y4_df = pd.read_html(y4_link)[0]
    
    # Drop unnecessary columns
    for df in [y1_df, y2_df, y3_df, y4_df]:
        df.drop(
            [
                '20 YR', '30 YR', 'Extrapolation Factor', '8 WEEKS BANK DISCOUNT',
                'COUPON EQUIVALENT', '52 WEEKS BANK DISCOUNT', 'COUPON EQUIVALENT.1'
            ],
            axis = 1,
            inplace = True
        )
    
    # Concat the data frames
    df = pd.concat([y1_df, y2_df, y3_df, y4_df], axis=0)
    df.reset_index(inplace = True, drop = True)
    
    # Clean up the date column
    df.Date = pd.to_datetime(df.Date, format="%m/%d/%Y")
    df.sort_values(by='Date', ascending=True, inplace=True)
    df.reset_index(inplace=True, drop=True)

    # Create list of dates to collect
    # my_dates = [friday] + [friday + dt.timedelta(days=-i) for i in [7, 7 * 2, 7 * 4, 7 * 8,
    #                                                                 7 * 12, 7 * 24, 7 * 52,
    #                                                                 7 * 76, 7 * 104]]
    my_dates = [friday] + \
        [friday + dt.timedelta(days=-i) for i in [j for j in range(7)]] + \
            [friday + dt.timedelta(days=-i) for i in [7 * j for j in range(1, 158, 2)]]

    # my_keys  = ['This Week', '1wk Ago', '2wk Ago', '1mo Ago', '2mo Ago', '3mo Ago', '6mo Ago', '1y Ago', '1.5y Ago', '2y Ago']
    # my_keys  = [my_keys[-i] for i in range(1, len(my_keys) + 1)]
    
    # Clean the list of dates
    i = 0
    for dte in my_dates:
        i += 1
        while dte not in list(df.Date):
            dte += dt.timedelta(days=-1)
            my_dates[i - 1] = dte
            
    # Remove any duplicate dates
    my_dates = lst_unique(my_dates)
    
    # Subset yield curve data for desired dates
    df = df[df.Date.isin(my_dates)]
    df.reset_index(inplace=True, drop=True)
    
    return df

## Define `Yield_Plot` which will create the Yield Curve figure
def Yield_Plot(yield_df, art_lst, friday):
    """
    Use to create an interactive visual of US Yield Curve data over past two years.

    Parameters
    ----------
    yield_df : TYPE
        DESCRIPTION.
    art_lst : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    """
    CSdict  = {'type': 'surface', 'is_3d': True, 'colspan': 1, 'rowspan': 1}  # Candlestick plot specs
    TBdict2  = {"type": "table", 'colspan': 1, 'rowspan': 1}                   # Table specs
    
    specs = [[CSdict],
             [TBdict2]]
    subtitles = ['<em>US Yield Curve', 'Relevant Articles']
    
    # Create the figure object
    fig = make_subplots(
        rows = 2,
        cols = 1,
        # column_widths = [1.1, 1.4, 1.1],
        row_heights = [2, 1],
        horizontal_spacing = 0.05,
        vertical_spacing = 0.07,
        specs = specs,
        subplot_titles = subtitles,
    )
    
    # Update the report title and other attributes
    # report_dates = [my_date_to_str(friday + dt.timedelta(days=-7), [True, False]),
    #                 my_date_to_str(friday, [True, False])]
    # report_title = "Gral's Weekly Market Update"
    # report_descr = ' to '.join(report_dates)
    
    fig.update_layout(
        # title = f"<em>{report_title} | " + report_descr,
        # title_font_size = 28,
        template = 'seaborn',
        height = 1000,
        width = 1400,
        autosize = True,
        hovermode = 'x',
    )

    # Collect the appropiate colors for the box plots
    colors = px.colors.diverging.curl
    colors = colors[:4] + colors[-5:]
    
    # Add the 3D surface plot
    x_dat = yield_df.columns[1:]
    y_dat = yield_df.iloc[:, 0]
    z_dat = yield_df.iloc[:, 1:]
    
    curve = go.Surface(x=x_dat,
                       y=y_dat,
                       z=z_dat,
                       #name=y_dat,
                       colorscale='RdBu',
                       showscale=False,
                       contours = {
                           "x": {"show": True},  # "start": 1.5, "end": 2, "size": 0.04, "color":"white"},
                           "y": {"show": True},
                           "z": {"show": True}   # , "start": 0.5, "end": 1.8, "size": 0.05}
                       }
                       )

    fig.add_trace(curve, row = 1, col = 1)
    fig.update_traces(row = 1, col = 1,
                      contours_z = dict(show=True, usecolormap=True,
                                        highlightcolor="limegreen", project_z=True)
                      )
    fig.update_layout(
                      scene = {"xaxis": {"title": "Tenor", "nticks": 20},
                               "yaxis": {"title": "Closing Date"},
                               "zaxis": {"title": "Closing Yield", "nticks": 10},
#                               'camera_eye': {"x": 1, "y": 1, "z": 1},
                               "aspectratio": {"x": 0.8, "y": 1, "z": 0.5}}
                     )
    
    # Add drowdowns
    # button_layer_1_height = 1.12
    # button_layer_2_height = 1.065
    
    fig.update_layout(
        updatemenus=[
            # Buttons for changing plot type
            # dict(
            #     type = "buttons",
            #     direction = "left",
            #     buttons=list([
            #         dict(
            #             args2=[{"type": ["surface", "table"]}],
            #             args=[{"colspan": [2, 1]}],
            #             label="3D Surface",
            #             method="restyle"
            #         ),
            #         dict(
            #             args2=[{"type": ["heatmap", "table"]}],
            #             args=[{"colspan": [2, 1]}],
            #             label="Heatmap",
            #             method="restyle"
            #         )
            #     ]),
            #     pad={"r": 5, "t": 5},
            #     showactive=True,
            #     x=0.1,
            #     xanchor="left",
            #     y=-0.2,
            #     yanchor="bottom"
            # ),
            ## Buttons for changing color scale
            dict(
                buttons=list([
                    dict(
                        args=[{"colorscale": ["RdBu", None]}],
                        label="Red-Blue",
                        method="restyle"
                    ),
                    dict(
                        args=[{"colorscale": ["Cividis", None]}],
                        label="Cividis",
                        method="restyle"
                    ),
                    dict(
                        args=[{"colorscale": ["Viridis", None]}],
                        label="Viridis",
                        method="restyle"
                    ),
                    dict(
                        args=[{"colorscale": ["Greens", None]}],
                        label="Greens",
                        method="restyle"
                    ),
                ]),
                type = "buttons",
                direction="right",
                pad={"r": 5, "t": 5},
                showactive=True,
                x=0.1,
                xanchor="left",
                y=-0.125,
                yanchor="bottom"
            ),
            ## Button for reversing color scale
            dict(
                buttons=list([
                    dict(
                        args=[{"reversescale": [False, None]}],
                        label="False",
                        method="restyle"
                    ),
                    dict(
                        args=[{"reversescale": [True, None]}],
                        label="True",
                        method="restyle"
                    )
                ]),
                type = "buttons",
                direction="right",
                pad={"r": 5, "t": 5},
                showactive=True,
                x=0.4,
                xanchor="left",
                y=-0.125,
                yanchor="bottom"
            ),
        ]
    )
    # Add annotations for buttons
    fig.update_layout(
        annotations=[
            # dict(
            #     text="Trace Type", x=0.05, xref="x domain", y=-0.2,
            #     yref="y domain", align="left", showarrow=False
            # ),
            dict(
                text='<em>Yield Curve', x=0.3, y=1,
                xref="paper", yref="paper", showarrow=False
            ),
            dict(
                text='Relevant Articles', x=0.9, y=1,
                xref="paper", yref="paper", showarrow=False
            ),
            dict(
                text="Color<br>Scale", x=0.05, xref="x domain",
                y=-0.125, yref="y domain", showarrow=False
            ),
            dict(
                text="Reverse<br>Colorscale", x=0.37, xref="x domain",
                y=-0.125, yref="y domain", showarrow=False
            ),
        ]
    )
    
    # Collect the articles table
    articles = plotly_article_table('YIELD', art_lst)
            
    ## Add the articles table
    # Create a list of fill colors for the table cells
    cell_fill_color = ['whitesmoke'] * 3
    head_fill_color = ['palegoldenrod'] * 3

    # Create the table object to be added to the figure
    table = go.Table(
        header = dict(
            values     = list(articles.columns),
            font       = dict(size=14, color='black'),
            line_color = None,
            fill_color = head_fill_color,
            align      = 'left'
        ),
        cells  = dict(
            values     = [articles[col] for col in articles.columns],
            font       = dict(size=12, color='black'),
            line_color = None,
            fill_color = cell_fill_color,
            align      = 'left',
            height     = 25
        ),
        columnwidth = [1, 1, 1.6],
    )
    
    fig.add_trace(table, row = 2, col = 1)
    
    return fig
