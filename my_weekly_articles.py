# -*- coding: utf-8 -*-
"""
Created on Fri Jun 11 21:38:36 2021

This script will collect 5 of the most "relevant" articles over the past week for each topic.
The 5 articles will be collected with 2 being from general Google searches, and one from each
of the following; Bloomberg, Seeking Alpha, WSJ.
As the article sources imply, these topics should be finance related.
If the topic is crypto related, 3 articles will be collected from coindesk.com,
1 from bloomberg, and 1 from Google.

@author: grega
"""
## Import selenium for web scraping
from selenium import webdriver

## Import standard python libraries
import pandas as pd    # For working with data frames
import re, os          # Regular expressions (re), and standard shell commands (os)
from os import path    # Create paths to save .txt files
import time            # Use .sleep() to make scraping sites smoother
import datetime as dt  # Working with dates in python

## Import the nltk library and classes needed for NLP work
import nltk
from nltk import PorterStemmer
from nltk.sentiment import SentimentIntensityAnalyzer


def my_str_to_date(str):
    return dt.datetime.strptime(str, "%a %d-%m-%y").date()

def my_date_to_str(date, title_format=[False, False]):
    if title_format[0]:
        if title_format[1]:
            return dt.datetime.strftime(date, "%a %d-%B-%y (Week: %U)")
        else:
            return dt.datetime.strftime(date, "%a %d-%B-%y")
            
    else:
        return dt.datetime.strftime(date, "%a %d-%m-%y")

def EndOfWeek(include_monday=False):
    today = dt.date.today()
    wkday = today.weekday()

    days_til = 4 - wkday
    end      = dt.date(today.year, today.month, today.day + days_til).strftime("%a %d-%m-%y")

    if include_monday:
        start    = dt.date(today.year, today.month, today.day - wkday).strftime("%a %d-%m-%y")
        return [start, end]
    else:
        return [end]

def my_topic(tick):
    topics = {
        '^GSPC': 'SP 500 US Markets',
        '^DJI': 'Dow Jones Industrial Average',
        '^IXIC': 'NASDAQ',
        'VTI': 'Vanguard VTI',
        'VEU': 'Vanguard VEU Global Markets',
        'VDE': 'Vanguard VDE Energy Markets',
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

class index_topic:
    
    def __init__(self, asset_class, topic):
        ## Assign inputs as class attributes
        self.asset_class = asset_class
        self.topic       = topic

        ## Initiate `Firefox` browser and access the desired website to create an article index for.
        ## Currently, this is really only works perfectly for specific sections of coindesk.com
        ## I also could add functionality to work across multiple browsers such as chrome, edge, safari...
        fp = webdriver.FirefoxProfile()

        ## Open the browser and go to the desired news page to scrape.
        ## This should not be the home page for the website. It should be a specific section
        ## of the news site which itself is their own index of articles related to the desired category.
        driver = webdriver.Firefox(firefox_profile=fp)
        driver.get("https://www.google.com")

        self.driver = driver        
        
    def topic_sources(self):
        ## Determine relevant sources for topic.
        ## Also determine regex search patterns for indexing source's.
        ## Assign results as class attributes.
        
        def coindesk():
            source_site     = ['https://www.coindesk.com', '/category/markets']
            article_pattern = '<div class="card-text-block">.*?</div>|<div class="list-item-card post">.*?</div>'
            title_pattern   = "<a title=.*? href=.+?>"
            link_pattern    = 'href=".*?"'
            date_pattern    = '<span class="card-date">.*?</span>|<time class="time">.*?</time>'
            sub_pattern     = ['<a title="|"|href=".*?"|>', 'href=|"', '<.*?>']
            
            return {'source_site': source_site,
                    'article_pattern': article_pattern,
                    'title_pattern': title_pattern,
                    'date_pattern': date_pattern,
                    'link_pattern': link_pattern,
                    'sub_pattern': sub_pattern}
        
        def bloomberg():
            source_site     = 'https://www.coindesk.com/category/markets'
            article_pattern = '<div class="card-text-block">|<div class="list-item-card post">.*?</div>'
            title_pattern   = "<a title=.*? href=.+?>"
            date_pattern    = '<span class="card-date">.*?</span>|<time class="time">.*?</time>'
            link_pattern    = 'href=".*?"'
            sub_pattern     = ['', '', '']
            
            return {'source_site': source_site,
                    'article_pattern': article_pattern,
                    'title_pattern': title_pattern,
                    'date_pattern': date_pattern,
                    'link_pattern': link_pattern,
                    'sub_pattern': sub_pattern}

        def google():
            source_site     = 'https://news.google.com/search?q='
            article_pattern = '<article class=".*?>.*?</article>|<div class="list-item-card post">.*?</div>'
            title_pattern   = '<h(\d){1,2} .*?><a href="./articles/.*?">.*?</h(\d){1,2}>|' + \
                              '<h(\d){1,2} .*?><a class=".*?" href="./articles/.*?">.*?</h(\d){1,2}>'
            date_pattern    = 'datetime=".*?"'  # '<time class=".*?>.*?</time>'
            link_pattern    = '<a class=".*?".*href=".*?" .*?></a>'
            source_pattern  = '<a href="./publications/.*?" data-n-tid=".*?">.*?</a>|<a class=".*?" href="./publications/.*?" data-n-tid=".*?">.*?</a>'
            sub_pattern     = ['<.*?>', 'href="|"', 'datetime="|T.*?"|"', '<.*?>']
                            # [  title,            link,                              date, publisher]
            
            return {'source_site': source_site,
                    'article_pattern': article_pattern,
                    'title_pattern': title_pattern,
                    'date_pattern': date_pattern,
                    'link_pattern': link_pattern,
                    'source_pattern': source_pattern,
                    'sub_pattern': sub_pattern}

        def seeking_alpha():
            source_site     = ['https://seekingalpha.com', '/search?list=all&q=', '&tab=headlines']
            article_pattern = '<article class=".*?>.*?</article>'
            title_pattern   = '<a class=".*?" href="/(article|news)/.*?">.*?</a>'
            date_pattern    = '<span class=".*?" data-test-id="post-list-date">.*?</span>'
            link_pattern    = 'href=".*?"'
            sub_pattern     = ['<.*?>', 'href=|"','<.*?>']
            
            return {'source_site': source_site,
                    'article_pattern': article_pattern,
                    'title_pattern': title_pattern,
                    'date_pattern': date_pattern,
                    'link_pattern': link_pattern,
                    'sub_pattern': sub_pattern}

        def wsj():
            source_site     = ['https://www.wsj.com', '/search?query=', '&mod=searchresults_viewallresults']
            article_pattern = '<article class=".*?>.*?</article>'
            title_pattern   = '<a class="" href=".*?"><span class="WSJTheme--headlineText-.*?">.*?</span>'
            date_pattern    = '<p class="WSJTheme--timestamp-.*?">.*?</p>'
            link_pattern    = 'href=".*?"'
            sub_pattern     = ['', '', '']
            
            return {'source_site': source_site,
                    'article_pattern': article_pattern,
                    'title_pattern': title_pattern,
                    'date_pattern': date_pattern,
                    'link_pattern': link_pattern,
                    'sub_pattern': sub_pattern}
        
        def my_patterns(source):
            source = source.lower()
            if source == 'coindesk':
                return coindesk()
            elif source == 'bloomberg':
                return bloomberg()
            elif source == 'google':
                return google()
            elif source == 'seeking_alpha':
                return seeking_alpha()
            elif source == 'wsj':
                return wsj()
        
        ## Collect necessary attributes
        driver      = self.driver
        asset_class = self.asset_class
        topic       = self.topic
        
        ## Determine the sources and define regex search patterns for pages
        if asset_class.lower() == 'crypto':
            sources = ['coindesk', 'coindesk', 'coindesk', 'seeking_alpha', 'google']
        elif asset_class.lower() == 'equity':
            sources = ['seeking_alpha', 'seeking_alpha', 'google', 'google', 'google']
        elif asset_class.lower() == 'fi':
            sources = ['bloomberg', 'seeking_alpha', 'wsj', 'google', 'google']
        
        ## Create a dictionary of appropiate patterns for each source
        patterns = {}
        for source in sources:
            patterns[source] = my_patterns(source)
        
        self.sources  = sources
        self.patterns = patterns       
        
    def index_sources(self):
        ## Scrape the desired sources for article.
        ## Assign article sources, titles, dates, links as a pandas df.
        driver      = self.driver
        asset_class = self.asset_class
        topic       = self.topic
        sources     = self.sources
        patterns    = self.patterns
        
        ## Iterate over the sources to collect article titles, links, and publishing dates
        source_articles = {}
        for source in sources:
            # Determine if the links have already been collected from parent source
            if source not in source_articles.keys():
                
                # Determine which page to go to
                if source in ['seeking_alpha', 'wsj']:
                    goto_site = ''.join(patterns[source]['source_site'][:2]) + my_topic(topic).replace('&', '') + patterns[source]['source_site'][-1]
                elif source in ['google']:
                    goto_site = patterns[source]['source_site'] + my_topic(topic).replace('&', '')
                else:
                    goto_site = ''.join(patterns[source]['source_site'])
                
                # Go to the page
                driver.get(goto_site)
                
                # Collect the article titles, links, publication dates
                articles = re.findall(patterns[source]['article_pattern'], driver.page_source)
                
                art_sources = []
                for art in articles:
                    
                    # Identify the article title, then the link, then clean both terms
                    art_title = re.search(patterns[source]['title_pattern'], art).group(0)
                    
                    # Identify the article link
                    if source.lower() in ['coindesk']:
                        art_link  = re.search(patterns[source]['link_pattern'], art_title).group(0)
                        art_link  = re.search('href=".*?"', art_link).group(0) if source.lower() == 'google' else art_link
                        
                    elif source.lower() in ['google']:
                        art_link  = re.search(patterns[source]['link_pattern'], art).group(0)
                        art_link  = re.search('href=".*?"', art_link).group(0) if source.lower() == 'google' else art_link                        

                    else:
                        art_link  = re.search(patterns[source]['link_pattern'], art).group(0)
                    
                    # Clean up title and link
                    art_title = re.sub(patterns[source]['sub_pattern'][0], '', art_title).strip()
                    art_link  = re.sub(patterns[source]['sub_pattern'][1], '', art_link).strip()
                    
                    # Attempt to recollect the article title if its the empty string
                    if art_title == '':
                        try:
                            art_title = re.findall('<a class=".*?" href="./articles/.*?">.*?</a>', art)[1]
                            art_title = re.sub(patterns[source]['sub_pattern'][0], '', art_title).strip()
                        except:
                            art_title = re.search(patterns[source]['title_pattern'], art).group(0).strip()
                    
                    # Identify the article publish date
                    try:
                        art_date  = re.search(patterns[source]['date_pattern'], art).group(0)
                        art_date  = re.sub(patterns[source]['sub_pattern'][2], '', art_date).strip()
                    except:
                        art_date  = str(dt.date.today())
                    
                    # Identify the article publisher (only relevant for Google)
                    if source.lower() == 'google':
                        
                        art_link  = "https://news.google.com" + art_link[1:]
                        
                        try:
                            art_publshr = re.search(patterns[source]['source_pattern'], art).group(0)
                            art_publshr = re.sub(patterns[source]['sub_pattern'][3], '', art_publshr).strip()
                                
                        except:
                            art_publshr = 'Google'
                            
                        art_sources.append([art_publshr, art_title, art_date, art_link])
                    
                    else:
                        art_link  = patterns[source]['source_site'][0] + art_link
                        art_sources.append([source, art_title, art_date, art_link])
                
                source_articles[source] = art_sources
        
        source_lst = []
        for source in source_articles.keys():
            temp_df = pd.DataFrame(source_articles[source], columns =['Source', 'Title', 'Date', 'Link'])
            source_lst.append(temp_df)
            
        index_df = pd.concat(source_lst, axis=0)
        
        driver.quit()
        
        self.driver          = driver
        self.source_articles = source_articles
        self.index_df        = index_df
    
    def clean_index_dates(self):
        index_df = self.index_df
        
        def my_clean_date(strDate):
            
            monday, friday = my_str_to_date(EndOfWeek(True)[0]), my_str_to_date(EndOfWeek(True)[1])
            clean_date = dt.date.today()
            
            # Check for key terms identifying the date of the post
            if 'today' in strDate.lower():
                clean_date = dt.date.today()
            elif 'yesterday' in strDate.lower():
                clean_date = dt.date.today() + dt.timedelta(days=-1)
            
            elif 'hours ago' in strDate.lower():
                clean_date = dt.date.today()
            
            elif 'monday' in strDate.lower():
                cleaned_date = monday
            elif 'tuesday' in strDate.lower():
                clean_date = monday + dt.timedelta(days=1)
            elif 'wednesday' in strDate.lower():
                clean_date = monday + dt.timedelta(days=2)
            elif 'thursday' in strDate.lower():
                clean_date = monday + dt.timedelta(days=3)
            elif 'friday' in strDate.lower():
                clean_date = friday
            elif 'saturday' in strDate.lower():
                clean_date = monday + dt.timedelta(days=5)
            elif 'sunday' in strDate.lower():
                clean_date = monday + dt.timedelta(days=-1)
            
            # Try to coerce the date string into a date object
            else:
                try:
                    clean_date = dt.datetime.strptime(strDate, "%Y-%m-%d")
                except ValueError:
                    try:
                        clean_date = dt.datetime.strptime(strDate[-12:], "%b %d, %Y")
                    except:
                        try:
                            clean_date = dt.datetime.strptime(strDate[-12:], "%a, %b. %d")
                        except:
                            try:
                                clean_date = dt.datetime.strptime(strDate[-12:], "%a, %B %d")
                            except:
                                try:
                                    clean_date = dt.datetime.strptime(strDate[-11:], "%a, %B %d")
                                except:
                                    try:
                                        clean_date = dt.datetime.strptime(strDate[-13:], "%b %d, %Y")
                                    except:
                                        try:
                                            clean_date = pd.to_datetime(strDate[-12:], infer_datetime_format=True)
                                        except:
                                            try:
                                                clean_date = pd.to_datetime(strDate[-11:], infer_datetime_format=True)
                                            except:
                                                clean_date = pd.to_datetime(strDate[-13:], infer_datetime_format=True)

            # Ensure the cleaned date object is actually a date object
            if type(clean_date) is not dt.date:
                clean_date = clean_date.date()
                
            # Ensure the appropiate year is assigned
            if clean_date.year == 1900:
                clean_date = dt.date(dt.date.today().year, clean_date.month, clean_date.day)
            
            return clean_date
        
        cleaned_dates = [my_clean_date(strDate) for strDate in index_df.Date]
        index_df.loc[:, 'Date'] = cleaned_dates
        
        self.index_df = index_df
    
    def go(self):
        self.topic_sources()
        self.index_sources()
        self.clean_index_dates()
        
        
class score_index:
    
    def __init__(self, asset_class, topic):
        ## Call the `index_topic` class for the topic.
        ## Assign the resulting class module as an attribute of this class.
        it = index_topic(asset_class, topic)
        it.go()
        
        self.asset_class = asset_class
        self.topic       = topic
        self.it          = it
        self.index_df    = it.index_df
        
    def LMcD_score(self):
        ## Score the article titles against the Loughran-McDonald NLP dictionary for finance.
        ## Append results to the df from `index_topic.index_sources` as new columns.
        ## Assign results as an updated pandas df with same attribute name.
        index_df = self.index_df
        
        ## Read in the Loughran-MacDonald dictionaries for NLP in finance
        LMcD_neg_url = 'https://raw.githubusercontent.com/AmeriFinn/NLP-Projects/main/LoughranMcDonald_Negative.csv'
        LMcD_pos_url = 'https://raw.githubusercontent.com/AmeriFinn/NLP-Projects/main/LoughranMcDonald_Positive.csv'
        
        LMcD_neg = list(pd.read_csv(LMcD_neg_url, index_col=0).index)
        LMcD_pos = list(pd.read_csv(LMcD_pos_url, index_col=0).index)
        
        ## Define function for scoring article titles against the dictionaries
        def score_title_lmcd(title, LMcD_dict):
            
            # Tokenize the title
            tokens = nltk.word_tokenize(title)
            
            # Clean the tokens
            keep_tokens = []
            for tok in tokens:
                if len(tok) > 1:
                    keep_tokens.append(tok.upper())
            
            # Count token matches against the provided dictionary
            score = 0
            for tok in keep_tokens:
                if tok.upper() in LMcD_dict:
                    score += 1
            
            return score
        
        ## Score each title
        index_df.loc[:, 'LMcD_Neg_Terms'] = index_df.Title.apply(
            lambda x: score_title_lmcd(x, LMcD_neg)
        )
        index_df.loc[:, 'LMcD_Pos_Terms'] = index_df.Title.apply(
            lambda x: score_title_lmcd(x, LMcD_pos)
        )
        index_df.loc[:, 'LMcD_Tot_Terms'] = index_df.apply(
            lambda x: x['LMcD_Neg_Terms'] + x['LMcD_Pos_Terms'],
            axis=1
        )
        
        self.index_df = index_df        
        
    def relevance_score(self):
        ## Score the article titles for "relevance". Relevance depends on LMcD score,
        ## publication date, and mention of specific terms. The specific terms will be
        ## determined in a fairly arbitrary manner for each topic by me.
        ## Append results to df from `LMcD_score` method.
        ## Assign updated df to the parent class attribute.

        ## Define function for scoring article titles against the dictionaries
        def score_title_topic(title, topic):
            
            # Tokenize the title
            # tokens = nltk.word_tokenize(title)
            topic_tokens  = nltk.word_tokenize(my_topic(topic))
            
            # # Clean the tokens
            # keep_tokens = []
            # # keep_topict = []
            # for tok in topic:
            #     if len(tok) > 1:
            #         keep_tokens.append(tok.upper())
                    
            # Create n-grams
            bigrams  = nltk.collocations.BigramCollocationFinder.from_words(topic_tokens)
            bigs_lst = bigrams.ngram_fd.most_common()
            bigs_lst = [' '.join(feature[0]) for feature in bigs_lst]
            
            trigrams  = nltk.collocations.TrigramCollocationFinder.from_words(topic_tokens)
            tris_lst = trigrams.ngram_fd.most_common()
            tris_lst = [' '.join(feature[0]) for feature in tris_lst]
            
            topic_tokens += bigs_lst + tris_lst
            
            # Count token matches against the provided topic
            score = 0
            for tok in topic_tokens:
                if tok.upper() in title.upper():
                    score += 1
            
            return score
        
        ## Collect the index df
        index_df = self.index_df
        topic    = self.topic
        
        ## Create datetime variables for monday and friday of this week
        monday, friday = my_str_to_date(EndOfWeek(True)[0]), my_str_to_date(EndOfWeek(True)[1])
        
        ## Score the articles for their date relevance
        index_df.loc[:, 'Date_Relevance'] = index_df.Date.apply(
            lambda x: ((friday - x).days - 7) * -1
            )
        
        ## Score the article titles for their topical relevance
        index_df.loc[:, 'Title_Relevance'] = index_df.Title.apply(
            lambda x: score_title_topic(x, topic)
            )
        
        self.index_df = index_df        
    
    def most_relevant(self):
        ## Determine the most relevant articles for each parent source.
        index_df = self.index_df
        
        ## Calculate a total score based on the selected relevancy scores
        index_df.loc[:, 'Relevancy_Score'] = index_df.apply(
            lambda x: (3 * x['LMcD_Tot_Terms']) + (0.5 * x['Date_Relevance']) + (5 * x['Title_Relevance']),
            axis = 1
        )
        
        ## Sort the index df by the most relevant articles
        index_df.sort_values(by='Relevancy_Score', ascending=False, inplace=True)
        index_df.reset_index(inplace=True, drop=True)
        
    def go(self):
        self.LMcD_score()
        self.relevance_score()
        self.most_relevant()
                
class scrape_index:
    pass

