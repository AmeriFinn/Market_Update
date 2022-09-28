# Weekly_Market_Report
The python scripts I use to create and publish a [financial markets update](https://cloud.datapane.com/reports/yklX1Qk/financial-markets-update/) on different financial assets such as the three major U.S. indexes, currencies, commodoties, bitcoin, and the U.S. Yield Curve.

Each page of the report covers a different asset and each page consists of a price chart, closing price quartiles over the past two years, holding period return data, and an index of artciles that have been scraped from Google News which have been deemed to be the most relevant articles for an asset. From the article index, the scripts will generate a text summary of the relevant articles in an attempt to summarize what has happened to the asset over the past few days.

The main scripts used to collect and summarize the price data are `EquityAnalysis.py`, `equity_plot.py`, and `yield_plot.py`. `EquityAnalysis.py` is a large script I wrote a couple years ago to collect asset prices and perform different calculations/analyses on an automated basis - however this script has not been revisited in some time...

The main script used to index, scrape, and summarize news articles is `my_weekly_articles.py`. It is the lengthiest script in the directory and has been the main development focus area.

If all files in the lib are saved to the same directory, the report can be made by executing the `Report_Master.py` script.

## High-priority to-do items
- Ensure no duplicate sentences are included in the article summaries. `my_weekly_articles.py`
- Refine scraping methods for websites/publishers which I have not made a scraping dictionary for in `mwr_utils.py`
- Continue tweaking/improving the scoring methods for articles in a Google News search. Ideally find a more algorithimic approach. `my_weekly_articles.py`

## Low-priority to-do items
- Update the Bloomberg scraping dictionary / figure out a reliable way to scrape these articles. `my_weekly_articles.py`
- Accurately collect publishing dates for articles that are hidden under a collapsed banner on the Google News page. `my_weekly_articles.py`
- Move the MACD overlaid chart to its own plot that is also linked to the dateslider. `equity_plot.py`
- Continue tweaking the datapane layout to improve readability on smaller monitors `dp_post.py`
