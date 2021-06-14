# -*- coding: utf-8 -*-
"""
EquityAnalysis is essentially a customized wrapper of the Yahoo Finance API, yfinance.

The Yahoo Finace API will be used to collect both the prices for inputted tickers and
the balance sheet data available through Yahoo.

** In order for this to work properly, and due to a simple but known error w/in
** the yfinance base.py file, the yfinance module must be re-installed using
** the following command:
    pip install git+https://github.com/rodrigobercini/yfinance.git

@author: Greg Allan, Bilal Omar, Clevland McCarty
"""

# Say Hello
print("Hello World")

## Import the standard libraries
import pandas as pd
import datetime as dt
#import numpy as np
import sys
# from IPython.display import clear_output
# import ipywidgets as widgets
# import plotly
import plotly.express as px

# Using Yahoo Finance API allows me to retrieve daily price info for equities,
# bonds, and options: (Open, High, Low, Close, Volume, Dividends, Stock Splits)
# Compared to the AlphaVantage API, yfinance allows for unlimited calls per
# day, but may be less efficent. It also has no technical indicator capability.
# Therfore, user-defined functions need to be utilized.
import yfinance as yf

# Create a pandas `IndexSlice` reference
idx = pd.IndexSlice

class Data:
    """
    .
    
    Parameters
    ----------
    None.
    
    Returns
    -------
    None.
    """
    
    def __init__(self, tickers, shares=[1], period="1y", interval="1wk"):
        """
        When `Data` is initialized, the list of tickers, the period.
        
        and the desired interval will be be appended to the `Data`
        class as attribute references.

        Parameters
        ----------
        tickers : list
            The list of ticker symbols that will be passed to the
            yahoo finance `download` class.

        shares : list
            A list denoting how many shares of each asset are held.
            This list must be the same lenght as the `tickers` list.

            If this list is too short, it will be expanded until it
            is of equal length to `tickers`. The value that is appended
            to this list will be the last value provided in the user input.

            If this list is too long, it will be trimmed to the length
            of `tickers` list.

        period : string, optional
            A string that can be passed to the `download` class,
            denoting what timeframe the data pull needs to span.

            The default is "1y".

            Options = ["1d", "5d",
                       "1mo", "3mo", "6mo",
                       "1y", "2y", "5y", "10y",
                       "ytd", "max"]

        interval : TYPE, optional
            A string denoting the interval for which data will be downloaded.

            The default is "1wk".

            Options = ["1m", "2m", "5m", "15m", "30m", "90m",
                       "1h",
                       "1d", "5d",
                       "1wk",
                       "1mo", "3mo"]

        Returns
        -------
        None.

        """
        ## Check user inputs for validity

        ## Check the `shares` inputs
        # Convert share inputs to integers
        shares = [int(a) if isinstance(a, (float, int)) == True else 1 for a in shares]
        # Check if `shares` and `tickers` are the same lengths
        if len(shares) > len(tickers):
            # Trim the `shares` list to the appropiate length
            shares = shares[:len(tickers)]
            
        elif len(shares) < len(tickers):
            # Extend the `shares` list until its length matches `tickers`
            while len(shares) != len(tickers):
                shares.append(shares[-1])
                
        # Zip the tickers and shares lists, then store in a dictionary
        shares = dict(zip(tickers,shares))

        # Create initial attributes for the `Data` class.
        self.tickers    = tickers       # List of tickers to be analyzed
        self.tick_count = len(tickers)  # Number of tickers
        self.shares     = shares        # Number of shares held for each ticker
        self.period     = period        # The user-inputted period (time-frame)
        self.interval   = interval      # The user-inputted interval of price data

    def Collect(self, DataType="both"):
        """
        `Collect` will collect price data and/or balance sheet data for the inputted tickers.
        
        Using the yfinance module, price data for all inputted tickers will
        be retrieved and then the following calculations will be performed:
            (1) Total Price of all tickers
            (2) Portfolio values based on inputted shares
            (3) YTD or Start-To-End returns
            (4) 5-period % change
            (5) 1-period % change
            
        Using the yfinance module (with the appropiately updated base.py file), 
        Financial Statement data will be retrieved for inputted equity tickers.

        Parameters
        ----------
        DataType : String
            A string denoting if `prices`, `balance sheet`, or `both` data sets
            should be collected.

        Returns
        -------
        self.PriceData               : pandas.DataFrame
            A DataFrame storing the share prices for the desired time interval
            and period of time.
        
        self.annual_financials       : pandas.DataFrame
            A DataFrame storing the `annual` financial statement provided
            by Yahoo Finance for each equity ticker.
            
        self.annual_cashflows        : pandas.DataFrame
            A DataFrame storing the `annual` cash flow statements provided
            by Yahoo Finacne for each equity ticker.
            
        self.annual_balance_sheet    : pandas.DataFrame
            A DataFrame storing the `annual` balance sheet statements provided
            by Yahoo Finacne for each equity ticker.

        self.quarterly_financials    : pandas.DataFrame
            A DataFrame storing the `quarterly` financial statement provided
            by Yahoo Finance for each equity ticker.
        
        self.quarterly_cashflows     : pandas.DataFrame
            A DataFrame storing the `quarterly` cash flow statements provided
            by Yahoo Finacne for each equity ticker.
        
        self.quarterly_balance_sheet : pandas.DataFrame
            A DataFrame storing the `quarterly` balance sheet statements provided
            by Yahoo Finacne for each equity ticker.
            
        self.Betas                   : Dictionary
            A dictionary of the 1-year beta's provided by Yahoo Finance for each
            inputted equity ticker.
        
        self.MarketCaps              : Dictionary
            A dictionary of the Market Capitalizations as of today for each 
            inputted equity ticker provided and calculated by Yahoo Finance.
        
        self.EnterpriseValues        : Dictionary
            A dictionary of the Enterprise Values as of today for each
            inputed equity ticker provided and claculated by Yahoo Finance.
        """
        if (DataType.upper() == "PRICES") | (DataType.upper() == "BOTH"):

            # Download the price data for the given tickers
            # Note : Using `yf.download` allows all ticker data to be
            #        downloaded simultaneously. Using `yf.Ticker` will
            #        require a loop over the `tickers` list which would
            #        be a much slower data collection process
            PriceData = yf.download(tickers  = self.tickers,
                                    period   = self.period,
                                    interval = self.interval)[['Open',
                                                               'Close',
                                                               'Adj Close',
                                                               'High',
                                                               'Low',
                                                               'Volume']] \
                        .sort_index(ascending=True)
            
            # Add a total price column
            PriceData['Adj Close', 'Total'] =\
                PriceData['Adj Close'].sum(axis=1)

            # Create columns for portfolio prices by multiplying the
            # Adj Close and number of shares held
            for col in [c for c in PriceData['Adj Close'].columns if c != 'Total']:
                PriceData[[('Portfolio_Value', col)]] = \
                   PriceData[[('Adj Close', col)]] * self.shares[col]

            # Add a total portfolio value column
            PriceData['Portfolio_Value', 'Total'] = \
                PriceData['Portfolio_Value'].sum(axis=1)

            for col in PriceData.columns:

                # Create columns for YTD or Start-To-End returns
                PriceData[[('YTD_Change', col[1])]] = \
                    PriceData[[('Adj Close', col[1])]] \
                        .fillna(method='bfill', inplace=False) \
                            .apply(lambda x: x/x.iloc[0] - 1) *100

            for col in PriceData.columns:

                # Create columns for a rolling % change over prior 5 periods
                PriceData[[('5per_Change', col[1])]] = \
                    PriceData[[('Adj Close', col[1])]] \
                    .pct_change(periods=5) * 100

            for col in PriceData.columns:

                # Create columns for a rolling % change over prior 1 period
                PriceData[[('PCT_Change', col[1])]] = \
                    PriceData[[('Adj Close', col[1])]] \
                    .pct_change(periods=1) * 100
            
            # Append the price results to the PriceData attribute of `Data`
            self.PriceData = round(PriceData,4)

        if (DataType.upper() == "BALANCE SHEET") | (DataType.upper() == "BOTH"):

            # Create empty storage lists for the Balance Sheet
            # and Cash FLow DataFrame's for all the equities
            quarterly_financials = []
            quarterly_cashflows  = []
            quarterly_BS         = []

            annual_financials    = []
            annual_cashflows     = []
            annual_BS            = []

            # Create empty dictionaries for Market Betas, Market Caps,
            # Enterprise Values, and outstanding shares for all of the equities
            Betas                = {}
            MarketCaps           = {}
            EnterpVals           = {}
            FloatShares          = {}

            # Initiate loop to collect B-S data for all tickers
            for tick in self.tickers:

                # Create a yfinance Ticker object for the given ticker
                yfTick = yf.Ticker(tick)

                if yfTick.info['quoteType'].upper() == 'EQUITY':

                    ## Collect relevant financial data provided by yfinance

                    # Collect the market beta for the given equity
                    if yfTick.info['beta'] != None:
                        Betas[tick] = yfTick.info['beta']
                    else:
                        Betas[tick] = 0

                    # Collect the Market Cap and Enterprise Value
                    MarketCaps[tick]  = yfTick.info['marketCap']
                    EnterpVals[tick]  = yfTick.info['enterpriseValue']
                    FloatShares[tick] = yfTick.info['floatShares']

                    # Collect the quartelry financial data
                    qFins = yfTick.quarterly_financials

                    # Create Multi-Index object for the quarterly
                    # financials data relative to the given ticker
                    qMIDX = pd.MultiIndex.from_tuples(
                        [(tick, dt.date.strftime(d, format="%Y-%m-%d")) for d in qFins.columns])
                    qFins.columns = qMIDX

                    # Collect the annual report financial data
                    aFins = yfTick.financials
                    # Create Multi-Index object for the annual
                    # financials data relative to the given ticker
                    aMIDX = pd.MultiIndex.from_tuples(
                        [(tick, dt.date.strftime(d, format="%Y-%m-%d")) for d in aFins.columns])
                    aFins.columns = aMIDX

                    # Append financails reults to storage lists which will be
                    # attached to the `Data` class object
                    quarterly_financials.append(qFins)
                    annual_financials.append(aFins)

                    ## Collect Cash Flow (CF) data

                    # Collect quarterly CF's data
                    qCFS = yfTick.quarterly_cashflow

                    # Create Multi-Index object for the quarterly
                    # CF's data relative to the given ticker
                    qMIDX = pd.MultiIndex.from_tuples(
                        [(tick, dt.date.strftime(d, format="%Y-%m-%d")) for d in qCFS.columns])
                    qCFS.columns = qMIDX

                    # Collect annuals CF's data
                    aCFS = yfTick.cashflow

                    # Create Multi-Index object for the annual
                    # CF's data relative to the given ticker
                    aMIDX = pd.MultiIndex.from_tuples(
                        [(tick, dt.date.strftime(d, format="%Y-%m-%d")) for d in aCFS.columns])
                    aCFS.columns = aMIDX

                    # Append CF reults to storage lists which will be attached to
                    # the `Data` class object
                    quarterly_cashflows.append(qCFS)
                    annual_cashflows.append(aCFS)

                    ## Collect Balance Sheet (B-S) data

                    # Collect the annual B-S
                    aBS = yfTick.balance_sheet

                    # Create Multi-Index object for the annual B-S data
                    aMIDX = pd.MultiIndex.from_tuples(
                        [(tick, dt.date.strftime(d, format="%Y-%m-%d")) for d in aBS.columns])

                    aBS.columns = aMIDX

                    # Collect the quarterly B-S
                    qBS = yfTick.quarterly_balance_sheet

                    # Create Multi-Index object for the annual B-S data
                    qMIDX = pd.MultiIndex.from_tuples(
                        [(tick, dt.date.strftime(d, format="%Y-%m-%d")) for d in qBS.columns])

                    qBS.columns = qMIDX

                    # Append B-S reults to storage lists which will be attached to
                    # the `Data` class object
                    annual_BS.append(aBS)
                    quarterly_BS.append(qBS)

                else:
                    # If the iterated ticker is not identified as an equity by
                    # Yahoo Finance, then this ticker must be skipped
                    print(f"{tick} is not a known equity. It must be an index, ETF, or non-existent." + \
                        "\n\tNo Balance Sheet Data will be collected.")

            # Append data results to the `Data` class object
            self.annual_financials       = pd.concat(annual_financials, axis = 1)
            self.annual_cashflows        = pd.concat(annual_cashflows, axis = 1)
            self.annual_balance_sheet    = pd.concat(annual_BS, axis = 1)

            self.quarterly_financials    = pd.concat(quarterly_financials, axis = 1)
            self.quarterly_cashflows     = pd.concat(quarterly_cashflows, axis = 1)
            self.quarterly_balance_sheet = pd.concat(quarterly_BS, axis = 1)

            self.Betas                   = Betas
            self.MarketCaps              = MarketCaps
            self.EnterpriseValues        = EnterpVals
            self.SharesOutstanding       = FloatShares

    def Forecast(self, TaxRate = 0.21):
        """
        `Forecast` will loop through the balance sheet and cashflow.
        
        statements that have been collected for the portfolio to
        forecast revenue and earnings growth. Then a WACC will be
        estimated from publicly available data to use in a Discounted
        Cash Flow model to calculate the intrinsic value of each equity.

        Returns
        -------
        None.

        """
        # Chech that the annual_financials class attribute has been defined
        if hasattr(self, 'annual_financials') == False:
            print(f"There is no Balance Sheet data attached to {self.__class__.__name__}." + \
                  "\nUse the `.Collect('both')` method before .Forecast.")
            sys.exit()

        # Append data needed for forecasting revenues to the `Data` class
        self.annual_earnings = self.annual_financials.loc['Total Revenue']
        self.annual_ebit     = self.annual_financials.loc['Ebit']
        self.ebit_margin     = self.annual_ebit / self.annual_earnings

        # Calculate the average EBIT Margin for each equity
        dictMarg = {}
        for i in self.ebit_margin.index.get_level_values(0).unique():
            tempEBIT    = self.ebit_margin.loc[idx[i,slice(None)]]
            Margin_i    = tempEBIT.mean()
            if round(Margin_i,6) > 0:
                dictMarg[i] = round(Margin_i,6)
            else:
                dictMarg[i] = tempEBIT[0]

        self.EBIT_Projected = dictMarg

        # Calculate the Compound Annual Growth Rate (CAGR) of Revenue for each firm
        dictCAGR = {}
        for i in self.annual_earnings.index.get_level_values(0).unique():
            tempCAGR    = self.annual_earnings.loc[idx[i,slice(None)]]
            CAGR_i      = (tempCAGR[0] / tempCAGR[-1]) ** float(1/tempCAGR.shape[0]) - 1
            dictCAGR[i] = round(CAGR_i,6)

        self.CAGR = dictCAGR

        # Collect the most recently reported annual earnings for simplicity
        # in calculating future revenues and earnings
        dictRevs = {}
        for i in self.annual_earnings.index.get_level_values(0).unique():
            temp = self.annual_earnings.loc[idx[i,slice(None)]]
            Rev_i = temp[0]
            dictRevs[i] = round(Rev_i,0)

        self.LastRevs = dictRevs

        # Forecast out `5` years of revenues and EBIT for each equity
        rngYrs   = range(1,6) # = [1,2,3,4,5]
        headers  = [f"Year_{x}" for x in rngYrs]
        dictProj = {}

        for i in self.LastRevs.keys():
            tempRevs = [self.LastRevs[i] * ((1+self.CAGR[i]))**x for x in rngYrs]
            dictProj[(i, "Annual Revenue")] = tempRevs

            tempEBIT = [Rev * self.EBIT_Projected[i] for Rev in tempRevs]
            dictProj[(i, "EBIT")] = tempEBIT

        # Convert the 5 year forecast to a data frame
        df = pd.DataFrame.from_dict(dictProj,
                                    orient  = "index",
                                    columns = headers)
        df.index = pd.MultiIndex.from_tuples(df.index)

        self.ProjectedFinancials = df

        # Collect the current Market Risk Premium for US equities
        MRPdf = pd.read_html('http://pages.stern.nyu.edu/' + \
                           '~adamodar/New_Home_Page/datafile/ctryprem.html')[0]
        MRPdf.columns = MRPdf.iloc[0]
        MRPdf         = MRPdf[1:]
        MRPdf.set_index('Country', inplace=True, drop=True)

        self.MRPdata = MRPdf
        self.MRP     = round(float(MRPdf.loc['United States'] \
                                   ['Equity Risk  Premium'][:-1])/100,6)

        # Collect the current 5-year risk free rate
        RFlst = pd.read_html('https://www.treasury.gov/resource-center/' + \
            'data-chart-center/interest-rates/Pages/TextView.aspx?data=yield')

        for lst in RFlst:
            # Find the needed DataFrame from the html data pull for risk-free rates
            if lst.columns[0] == 'Date':
                RFdf = lst
                break

        self.RFdata = RFdf
        #self.RFrate = ((1+(RFdf['5 yr'].iloc[-1]/100))**(1/5))-1
        self.RFrate = RFdf['5 yr'].iloc[-1]/100

        # Calculate the required return for each equity using CAPM
        reqRets = {}
        for tick in self.Betas.keys():
            reqRets[tick]    = round(self.RFrate + (self.Betas[tick] * self.MRP),6)
        self.RequiredReturns = reqRets

        # Calculte the cost of debt for each equity
        intExps = {}
        TotDebs = {}
        debCost = {}
        for tick in self.Betas.keys():
            intExp        = abs(self.annual_financials[tick].loc['Interest Expense'][0])
            intExps[tick] = round(intExp,0)

            TotDeb        = abs(self.annual_balance_sheet[tick].loc['Long Term Debt'][0])
            TotDebs[tick] = round(TotDeb,0)

            debCost[tick] = round(intExp / TotDeb, 6)

        self.InterestExpense = intExps
        self.TotalDebts      = TotDebs
        self.CostOfDebt      = debCost

        # Calculate the WACC for each equity
        WACCs = {}
        for tick in self.RequiredReturns.keys():
            EquityCost = self.RequiredReturns[tick]
            DebtCost   = self.CostOfDebt[tick]

            Mcap = self.MarketCaps[tick]
            Eval = self.EnterpriseValues[tick]

            EquityW = round(Mcap / Eval, 6)
            DebtW   = round((Eval - Mcap) / Eval ,6)

            WACCs[tick] = round((EquityCost * EquityW) + (DebtCost * DebtW * (1-TaxRate)),6)
        self.WACCs = WACCs

        # Finally discount the projected EBITs for each equity using the 
        # estimated WACC's for each equity ticker
        IntrinsicVal = {}
        LTGrowth = .01
        for tick in self.WACCs.keys():
            DCF_i = 0
            for i in range(1,5):
                DCF_i += self.ProjectedFinancials.loc[idx[tick,'EBIT'],f"Year_{i}"] \
                    / ((1 + self.WACCs[tick])**i)
            
            # Calculate and discount the terminal value
            # Note: LTGrowth is set to 1% until a more appropiate measure
            #       can be determined
            Terminal = self.ProjectedFinancials.loc[idx[tick,'EBIT'],"Year_5"] \
                / (self.WACCs[tick] - LTGrowth)
            DCF_i += Terminal / ((1 + self.WACCs[tick]) ** 5)
            
            # Calculate the intrinsic value for each equity ticker
            IntrinsicVal[tick] = DCF_i / self.SharesOutstanding[tick]
            
        self.IntrinsicValues = IntrinsicVal

class Plot:
    """
    .
    
    Parameters
    ----------
    None.
    
    Returns
    -------
    None.
    
    """
    
    def __init__(self, Data, PlotColumn, PlotType="Line",
                 Title = "", invertScatter=True):
        """
        On initiation, inputs will be assigned as class attributes.

        Parameters
        ----------
        Data : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        self.DataObj   = Data
        self.PriceData = Data.PriceData

        self.PlotColumn = PlotColumn
        self.PlotType   = PlotType

        self.PlotData = self.PriceData[PlotColumn]
        self.PlotData.reset_index(drop=False, inplace=True)

        if Title == "":
            Title = PlotColumn
        self.Title         = Title
        self.invertScatter = invertScatter

    def Plot(self, MarginStyle='box'):
        """
        .

        Parameters
        ----------
        MarginStyle : TYPE, optional
            DESCRIPTION. The default is 'box'.

        Returns
        -------
        figs : TYPE
            DESCRIPTION.

        """
        figs = []

        # Create plotyly line plot objects if the user has selected them
        if (self.PlotType.upper() == 'LINE') | (self.PlotType.upper() == 'ALL'):
            LineFig = px.line(data_frame = self.PlotData.dropna(axis=0),
                              x          = 'Date',
                              y          = [col for col in self.PlotData.columns],
                              title      = f'{self.Title} - Time Series | ' + \
                                  f'{self.DataObj.interval} interval - {self.DataObj.period} period')
            figs.append(LineFig)

        # Create plotly area plot objects if the user has selected them
        if (self.PlotType.upper() == 'AREA') | (self.PlotType.upper() == 'ALL'):
            AreaFig = px.area(data_frame = self.PlotData.dropna(axis=0),
                              x          = 'Date',
                              y          = [col for col in self.PlotData.columns if col != 'Total'],
                              hover_data = {'Total':True},
                              title      = f'{self.Title} - Area Plot' + ' | ' + \
                                  f'{self.DataObj.interval} interval - {self.DataObj.period} period')
            figs.append(AreaFig)

        # Create a descriptive stats table and scatter plot for the selected data
        if (self.PlotType.upper() == 'SCATTER') | (self.PlotType.upper() == 'ALL'):

            desc = self.PriceData['PCT_Change'].describe().loc[['mean', 'std'],:].T

            ytdD = self.PriceData['YTD_Change'].iloc[-1].rename('Full Return')
            pctD = self.PriceData['PCT_Change'].iloc[-1].rename('One Period Return')
            cloD = self.PriceData['Adj Close'].iloc[-1].rename('Close')
            porD = self.PriceData['Portfolio_Value'].iloc[-1].rename('Port_Value')

            scat = pd.concat([desc,ytdD,pctD,cloD,porD], axis=1)
            scat.reset_index(inplace=True, drop=False)
            scat.rename(columns={'index':'Ticker','mean':'Mean','std':'SD'},
                        inplace=True)

            if self.invertScatter == True:
                xDat = 'SD'
                yDat = 'Mean'
            else:
                xDat = 'Mean'
                yDat = 'SD'

            ScatFig = px.scatter(data_frame = scat,
                                 x          = xDat,
                                 y          = yDat,
                                 hover_name = 'Ticker',
                                 color_continuous_midpoint = 'cyan',
                                 text       = 'Ticker',
                                 hover_data = ['Close', 'Full Return', 'One Period Return'],
                                 trendline  = 'ols',
                                 trendline_color_override = 'darkcyan',
                                 marginal_x = MarginStyle,
                                 marginal_y = MarginStyle,
                                 size       = 'Port_Value',
                                 opacity    = 0.5,
                                 title      = f'Single Period Returns, {xDat} vs. {yDat}' + ' | ' + \
                                     f'{self.DataObj.interval} interval - {self.DataObj.period} period')
            #ScatFig.update_traces(textposition='top center')
            figs.append(ScatFig)

        return figs