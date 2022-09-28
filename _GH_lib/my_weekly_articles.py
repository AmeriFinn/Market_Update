# -*- coding: utf-8 -*-
"""
Created on Fri Jun 11 21:38:36 2021.

This script will scrape and analyze the most "relevant" news articles for each desired topic.

Topics covered are various financial assets such as equity indexes, foreign exchange, commodities,
bitocin, and the yield curve.

News articles are first indexed from a Google News search. Then the relevancy of each article
is determined based on how recently it was published, a sentimenet score of the article title
based on the Loughran McDonald NLP Dictionary for Finance, a similarity score for the artcile
title based on the custom-defined relevancy dictionary in the `my_topic` function of the
`mwr_utils` module, and a preference score of the article publisher.

After the articles are indexed, and the desired number of most "relevant" articles have been
scraped, each article will be summarized and then a summary of the summaries will be generated.

@author: grega
"""
## Import selenium for web scraping
from selenium import webdriver
from selenium.common.exceptions import InvalidArgumentException, WebDriverException
# from selenium.webdriver.common.by import By

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
from nltk.corpus import stopwords
from nltk.cluster.util import cosine_distance

## Import the additional NLP libraries to be incorporated through the script
from textblob import TextBlob

## Import other fairly standard libraries
import numpy as np
import networkx as nx
import calendar

## Import the necessary functions from mwr_utils
from mwr_utils import my_str_to_date, EndOfWeek, my_topic

pd.set_option('display.max_columns', 6)
pd.set_option('display.max_colwidth', 15)
pd.set_option('display.expand_frame_repr', False)

class index_topic:
    """Creates an index of relevant articles that can than be scraped for a given topic."""
    
    def __init__(self, asset_class, topic, driver=None):
        """
        Initialize the class and a selenium webdriver object to create an article index.
        
        Parameters
        ----------
        asset_class : str
            The asset class (i.e. equities, fixed income, commodities, crypto) that the topic
            fits into.
        topic : str
            The specific asset or topic that we want to analyze market sentiment for.
        driver : selenium.webdriver, optional
            A selenium webbrowser object. The default is None.
            
        Returns
        -------
        None.
        
        """
        ## Assign inputs as class attributes
        self.asset_class = asset_class
        self.topic       = topic
        
        ## Initiate `Firefox` browser and access the desired website to create an article index for.
        ## Currently, this is really only works perfectly for specific sections of coindesk.com
        ## I also could add functionality to work across multiple browsers such as chrome or edge
        fp = webdriver.FirefoxProfile()
        
        # Open a web browser and go to google
        if driver is None:
            driver = webdriver.Firefox(firefox_profile=fp)
            driver.maximize_window()
            driver.get("https://www.google.com")
            
            # self.close_driver = True
        # else:
        self.close_driver = False
        self.driver = driver
        
    def topic_sources(self):
        """
        Define dictionaries used to scrape key elements of article headlines from various websites.
        
        Determine relevant sources for topic.
        Also determine regex search patterns for indexing source's.
        Assign results as class attributes.
        
        Returns
        -------
        dict
            A dictionary of html patterns to search for in an article on a given website.
            
        """
        def coindesk():
            """Define a dict of html patterns on coindesk.com."""
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
            """Define a dict of html patterns on bloomberg.com."""
            source_site     = 'https://www.bloomberg.com'
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
            """Define a dict of html patterns on news.google.com."""
            source_site     = 'https://news.google.com/search?q='
            article_pattern = '<article class=".*?>.*?</article>|<div class="list-item-card post">.*?</div>'
            title_pattern   = '<h(\d){1,2} .*?><a href="./articles/.*?">.*?</h(\d){1,2}>|' + \
                              '<h(\d){1,2} .*?><a class=".*?" href="./articles/.*?">.*?</h(\d){1,2}>'
            date_pattern    = 'datetime=".*?"'  # '<time class=".*?>.*?</time>'
            link_pattern    = '<a class=".*?".*href=".*?" .*?></a>'
            source_pattern  = '<a href="./publications/.*?" data-n-tid=".*?">.*?</a>|' + \
                              '<a class=".*?" href="./publications/.*?" data-n-tid=".*?">.*?</a>|' + \
                              '</svg><a class=".*?" data-n-tid=".*?">.*?</a>'
            sub_pattern     = ['<.*?>', 'href="|"', 'datetime="|T.*?"|"', '<.*?>']
            
            return {'source_site': source_site,
                    'article_pattern': article_pattern,
                    'title_pattern': title_pattern,
                    'date_pattern': date_pattern,
                    'link_pattern': link_pattern,
                    'source_pattern': source_pattern,
                    'sub_pattern': sub_pattern}
        
        def seeking_alpha():
            """Define a dict of html patterns on seekingalpha.com."""
            source_site     = ['https://seekingalpha.com', '/search?list=all&q=', '&tab=headlines']
            article_pattern = '<article class=".*?>.*?</article>'
            title_pattern   = '<a class=".*?" href="/(article|news)/.*?">.*?</a>'
            date_pattern    = '<span class=".*?" data-test-id="post-list-date">.*?</span>'
            link_pattern    = 'href=".*?"'
            sub_pattern     = ['<.*?>', 'href=|"', '<.*?>']
            
            return {'source_site': source_site,
                    'article_pattern': article_pattern,
                    'title_pattern': title_pattern,
                    'date_pattern': date_pattern,
                    'link_pattern': link_pattern,
                    'sub_pattern': sub_pattern}
        
        def wsj():
            """Define a dict of html patterns on wsj.com."""
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
            """Collect and return relevant html pattern dict based on the article source."""
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
        
        asset_class = self.asset_class
        
        ## Determine the sources and define regex search patterns for pages
        if asset_class.lower() == 'crypto':
            sources = ['coindesk', 'coindesk', 'coindesk', 'seeking_alpha', 'google']
        elif asset_class.lower() == 'equity':
            # sources = ['seeking_alpha', 'seeking_alpha', 'google', 'google', 'google']
            sources = ['google', 'google', 'google', 'google', 'google']
        elif asset_class.lower() == 'fi':
            sources = ['bloomberg', 'seeking_alpha', 'wsj', 'google', 'google']
        
        ## Create a dictionary of appropiate patterns for each source
        patterns = {}
        for source in sources:
            patterns[source] = my_patterns(source)
        
        self.sources  = sources
        self.patterns = patterns
        
    def index_sources(self):
        """
        Create an article index by scraping headlines, dates, and sources from news.google.com.
        
        Assign the resulting index as a class attribute structured as a pd.DataFrame.
        
        Returns
        -------
        None.
        
        """
        driver      = self.driver
        # asset_class = self.asset_class
        topic       = self.topic
        sources     = self.sources
        patterns    = self.patterns
        
        # Expand any collapsed sections of the search
        # btns = re.findall(
        #     '<div.*?aria-label="Show more articles for this story" aria-disabled="false".*?</div>',
        #     driver.page_source
        # )
        
        ## Iterate over the sources to collect article titles, links, and publishing dates
        source_articles = {}
        for source in sources:
            # Collect articles and links if the links haven't already
            # been collected from parent source
            if source not in source_articles.keys():
                
                # Determine which page to go to
                if source in ['seeking_alpha', 'wsj']:
                    goto_site = ''.join(patterns[source]['source_site'][:2]) + \
                        my_topic(topic).replace('&', '') + patterns[source]['source_site'][-1]
                        
                elif source == 'google':
                    goto_site = patterns[source]['source_site'] + my_topic(topic).replace('&', '')
                
                else:
                    goto_site = ''.join(patterns[source]['source_site'])
                
                # Go to the page
                driver.get(goto_site)
                
                # Collect the article titles, links, publication dates
                articles = re.findall(patterns[source]['article_pattern'], driver.page_source)
                
                # Iterate over the list of articles identified to collect cleaned data
                art_sources = []
                for art in articles:
                    
                    # Identify the article title, then the link, then clean both terms
                    art_title = re.search(patterns[source]['title_pattern'], art).group(0)
                    
                    # Identify the article link
                    if source.lower() == 'coindesk':
                        art_link  = re.search(patterns[source]['link_pattern'], art_title).group(0)
                        art_link  = re.search('href=".*?"', art_link).group(0) \
                            if source.lower() == 'google' else art_link
                        
                    elif source.lower() == 'google':
                        art_link  = re.search(patterns[source]['link_pattern'], art).group(0)
                        art_link  = re.search('href=".*?"', art_link).group(0) \
                            if source.lower() == 'google' else art_link
                            
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
                            
                        except (KeyError, AttributeError):
                            art_title = re.search(patterns[source]['title_pattern'], art).group(0).strip()
                    
                    # Identify the article publish date
                    try:
                        art_date  = re.search(patterns[source]['date_pattern'], art).group(0)
                        art_date  = re.sub(patterns[source]['sub_pattern'][2], '', art_date).strip()
                    
                    except (KeyError, AttributeError):
                        # TODO
                        # Determine the best approach here. Option 1 is to make the risky
                        # assumption. Option 2 is to not collect the article.
                        
                        # Make an assumption that if the date could not be identified, that it
                        # was published today. Bit of a risky assumption...
                        # art_date  = str(dt.date.today())  # Option 1
                        
                        continue  # Option 2
                    
                    # Identify the article publisher (only relevant for Google)
                    if source.lower() == 'google':
                        
                        art_link  = "https://news.google.com" + art_link[1:]
                        
                        try:
                            art_publshr = re.search(patterns[source]['source_pattern'], art).group(0)
                            art_publshr = re.sub(patterns[source]['sub_pattern'][3], '', art_publshr).strip()
                                
                        except (KeyError, AttributeError):
                            # If the publisher could not be identified, use Google as the default
                            # This is not ideal but considering I can't find a way to automate the
                            # process of expanding buttons on news.google.com it's the best solution
                            # I have currently. I can incorporate functionality to update the
                            # publisher data in a similar manner to how I update article links.
                            art_publshr = 'Google'
                            # Unlike instances where the article publishing date can't be collected,
                            # this can be resolved once the article itself is scraped. Conversely,
                            # I do not currently have reliable keys in the `pattern` dictionary
                            # to identify publishing dates across dozens of different websites
                            
                        art_sources.append([art_publshr, art_title, art_date, art_link])
                    
                    else:
                        art_link  = patterns[source]['source_site'][0] + art_link
                        art_sources.append([source, art_title, art_date, art_link])
                
                source_articles[source] = art_sources
        
        # Create a pandas df for each dictionary created above and then merge all df's into one
        source_lst = []
        for source in source_articles.keys():
            temp_df = pd.DataFrame(source_articles[source], columns =['Source', 'Title', 'Date', 'Link'])
            source_lst.append(temp_df)
            
        index_df = pd.concat(source_lst, axis=0)
        
        # Close the driver if the user only wants to create an article index.
        if self.close_driver:
            driver.quit()
        
        self.driver          = driver
        self.source_articles = source_articles
        self.index_df        = index_df
    
    def clean_index_dates(self):
        """
        Clean up the publishing dates collected to convert them into a datetime acceptable format.
        
        Returns
        -------
        None.
        """
        index_df = self.index_df
        
        def my_clean_date(strDate):
            """Convert the date string into a datetime object."""
            monday     = my_str_to_date(EndOfWeek(True)[0])
            friday     = my_str_to_date(EndOfWeek(True)[1])
            clean_date = dt.date.today()
            
            # Check for key terms identifying the date of the post
            if 'today' in strDate.lower():
                clean_date = dt.date.today()
            elif 'yesterday' in strDate.lower():
                clean_date = dt.date.today() + dt.timedelta(days=-1)
            
            elif 'hours ago' in strDate.lower():
                clean_date = dt.date.today()
            
            elif len(re.findall('\d{1,2} days ago', strDate)) > 0:
                print(f'\n{strDate}')
                input('.. days ago pattern found\n')
            
            elif 'monday' in strDate.lower():
                clean_date = monday
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
                    # date_formats = ["%b %d, %Y", "%a, %b. %d", "%a, %B %d",
                    #                 "%a, %B %d", "%b %d, %Y"]
                    # str_lengths  = [12, 12, 12, 11, 13]

                    # for frmt, i in zip(date_formats, str_lengths):
                    #     try:
                    #         clean_date = dt.datetime.strptime(strDate[-i:], frmt)
                    #         break
                    
                    #     except:
                    #         try:
                    #             clean_date = pd.to_datetime(strDate[-11:], infer_datetime_format=True)
                    #         except:
                    #             clean_date = pd.to_datetime(strDate[-13:], infer_datetime_format=True)

                    try:
                        clean_date = dt.datetime.strptime(strDate[-12:], "%b %d, %Y")
                    except ValueError:
                        try:
                            clean_date = dt.datetime.strptime(strDate[-12:], "%a, %b. %d")
                        except ValueError:
                            try:
                                clean_date = dt.datetime.strptime(strDate[-12:], "%a, %B %d")
                            except ValueError:
                                try:
                                    clean_date = dt.datetime.strptime(strDate[-11:], "%a, %B %d")
                                except ValueError:
                                    try:
                                        clean_date = dt.datetime.strptime(strDate[-13:], "%b %d, %Y")
                                    except ValueError:
                                        try:
                                            clean_date = pd.to_datetime(strDate[-12:], infer_datetime_format=True)
                                        except ValueError:
                                            try:
                                                clean_date = pd.to_datetime(strDate[-11:], infer_datetime_format=True)
                                            except ValueError:
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
        """Execute the three methods of this class."""
        self.topic_sources()
        self.index_sources()
        self.clean_index_dates()
              
class score_index:
    """Score the index that was created in `index_topic` class using Loughran-MacDonald dictionaries."""
    
    def __init__(self, asset_class, topic, driver=None):
        """
        Score the index that was created through the `index_topic` class.
        
        Parameters
        ----------
        asset_class : str
            The asset class (i.e. equities, fixed income, commodities, crypto) that the topic
            fits into.
        topic : str
            The specific asset or topic that we want to analyze market sentiment for.
        driver : selenium.webdriver, optional
            A selenium webbrowser object. The default is None.
            
        Returns
        -------
        None.
        
        """
        ## Call the `index_topic` class for the topic.
        ## Assign the resulting class module as an attribute of this class.
        it = index_topic(asset_class=asset_class, topic=topic, driver=driver)
        it.go()
        
        self.asset_class = asset_class
        self.topic       = topic
        self.it          = it
        self.index_df    = it.index_df
        self.driver      = it.driver
        
    def LMcD_score(self):
        """
        Score the article titles against the Loughran-McDonald NLP dictionary for finance.
        
        Append results to the df from `index_topic.index_sources` as new columns.
        Assign results as an updated pandas df with same attribute name.
        
        Returns
        -------
        None.
        
        """
        index_df = self.index_df
        
        ## Read in the Loughran-MacDonald dictionaries for NLP in finance
        LMcD_neg_url = 'https://raw.githubusercontent.com/AmeriFinn/NLP-Projects/main/LoughranMcDonald_Negative.csv'
        LMcD_pos_url = 'https://raw.githubusercontent.com/AmeriFinn/NLP-Projects/main/LoughranMcDonald_Positive.csv'
        
        LMcD_neg = list(pd.read_csv(LMcD_neg_url, index_col=0).index)
        LMcD_pos = list(pd.read_csv(LMcD_pos_url, index_col=0).index)
        
        ## Define function for scoring article titles against the dictionaries
        def score_title_lmcd(title, LMcD_dict):
            """
            Count the number of term matches between the given title and LMcD dictionary.
            
            Parameters
            ----------
            title : str
                The title collected from the Google news search.
            LMcD_dict : list
                The Loughran Macdonald dictionary of positive or negative terms to search for.
                This is structured as a list but I use dict in the name since its an NLP dictionary.
                
            Returns
            -------
            score : int
                The total term matches in the title with the Lour.
                
            """
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
        """
        Score the article titles for "relevance".
        
        Relevance depends on LMcD score, publication date, and mention of specific terms.
        The specific terms will be determined in a fairly arbitrary manner for each topic by me.
        Append results to df from `LMcD_score` method. Assign updated df to the parent class attribute.
        
        Returns
        -------
        None.
        
        """
        def score_title_topic(title, topic):
            """
            Score article titles against the the custom made relevance dictionaries.
            
            Parameters
            ----------
            title : str
                The article title.
            topic : str
                The topic/asset class related to the given asset.
                
            Returns
            -------
            score : int
                The number of relevant terms in the title.
                
            """
            # Tokenize the title
            # tokens = nltk.word_tokenize(title)
            topic_tokens  = nltk.word_tokenize(my_topic(topic))
            
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
        
        def score_publisher(publisher):
            """
            Score the article publisher so desired sources are more likely to be included.
            
            Parameters
            ----------
            publisher : str
                The publisher as displayed on new.google.com
            
            Returns
            -------
            int
                The relevancy score for the given article publisher.

            """
            # Define list of publishers with dicts defined in summarize_articles.scraping_keys
            # TODO - Update the bloomber scraping procedures to make it an ideal publisher
            ideal_pubs = [
                'coindesk', 'forbes', 'reuters', 'seeking alpha', 'yahoo finance',
                'the new york times', 'the wall street journal'
            ]
            # Define a second list of publishers with no defined dicts but still good publishers
            prfrd_pubs = [
                'nasdaq', "barron's", 'marketwatch', 'cnbc', 'morningstar',
                'cnn', 'fox business', 'zacks investment research', 'thestreet',
                'financial times', 'investing.com', 'dailyfx'
            ]
            
            # Determine what score to assign based on the publisher
            ## TODO
            ## Continue tweaking this calculation - or even better, find an algorithmic solution...
            if publisher.lower() in ideal_pubs:
                return 50
            elif publisher.lower() in prfrd_pubs:
                return 25
            else:
                return -25
            
        ## Collect the index df
        index_df = self.index_df
        topic    = self.topic
        
        ## Create datetime variables for monday and friday of this week
        monday, friday = my_str_to_date(EndOfWeek(True)[0]), my_str_to_date(EndOfWeek(True)[1])
        
        ## Score the articles for their date relevance
        index_df.loc[:, 'Date_Relevance'] = index_df.Date.apply(
            lambda x: min(((friday - x).days - 7) * -1, 7)
        )
        
        ## Score the article titles for their topical relevance
        index_df.loc[:, 'Title_Relevance'] = index_df.Title.apply(
            lambda x: score_title_topic(x, topic)
        )
        
        ## Score the articles based on who published them
        index_df.loc[:, 'Publisher_Score'] = index_df.Source.apply(
            lambda x: score_publisher(x)
        )
        
        self.index_df = index_df
    
    def most_relevant(self):
        """
        Determine the most relevant articles to be included in the report.
        
        Relevancy is calculated as the weighted sum of Loughran-MacDonald term matches,
        the date relevance (recency), and key term matches.
        
        Returns
        -------
        None.
        
        """
        def date_weight(date_score):
            """Define a function for calculating the weight for the Date Relevance."""
            ## TODO
            ## Continue tweaking this calculation - or even better, find an algorithmic solution...
            if date_score > 0:
                # Scale score so articles this week have a more uniform chance of being displayed
                return round(5 * np.log(date_score), 6)
            
            elif date_score < 0:
                # Scale score so older articles have lower chance of being displayed
                return -round(3 * np.exp((-1 * date_score)**.5), 6)
            
            else:
                return -0.5
            
        ## Determine the most relevant articles for each parent source.
        index_df = self.index_df
        
        ## Calculate a total score based on the selected relevancy scores
        ## TODO
        ## Continue tweaking this calculation - or even better, find an algorithmic solution...
        index_df.loc[:, 'Relevancy_Score'] = index_df.apply(
            lambda x: (20 * x['LMcD_Tot_Terms']) + \
                      (20 * x['Title_Relevance']) + \
                      (date_weight(x['Date_Relevance'])) + \
                      (x['Publisher_Score']),
            axis = 1
        )
        
        ## Sort the index df by the most relevant articles
        index_df.sort_values(by='Relevancy_Score', ascending=False, inplace=True)
        index_df.reset_index(inplace=True, drop=True)
        
    def go(self):
        """Execute the three methods of this class."""
        self.LMcD_score()
        self.relevance_score()
        self.most_relevant()

class summarize_articles:
    """The core class that will index, score, and summarize articles for a given asset class."""
    
    def __init__(self, asset_class, topic, top_n=15, driver=None):
        """
        Initialize this class, and `score_index` which also initializes `index_topic`.
        
        Parameters
        ----------
        asset_class : str
            The asset class that we want to analyze market sentiment for.
        topic : str
            A string denoting what topic to search.
        driver : selenium.webdriver, optional
            A selenium webbrowser object. The default is None.
            
        Returns
        -------
        None.
        
        """
        ## Assign inputs as attributes
        self.asset_class = asset_class
        self.topic       = topic
        self.top_n       = top_n
        
        ## Use `score_index` (which uses `index_topic`) to collect 10 relevant links
        si = score_index(asset_class, topic, driver)
        si.go()
        
        ## Assign index_df as an attribute
        self.index_df = si.index_df
        self.si       = si
        driver        = si.driver if si.driver is not None else driver
        
        ## Initiate `Firefox` browser and access the desired website to create an article index for.
        ## Currently, this is really only works perfectly for specific sections of coindesk.com
        ## I also could add functionality to work across multiple browsers such as chrome or edge
        fp = webdriver.FirefoxProfile()
        
        ## Open the browser and go to the desired news page to scrape.
        ## This should not be the home page for the website. It should be a specific section
        ## of the news site which itself is their own index of articles related to the desired category.
        if driver is None:
            driver = webdriver.Firefox(firefox_profile=fp)
            driver.maximize_window()
            driver.get("https://www.google.com")
            
            self.close_driver = True
        else:
            self.close_driver = False
                
        self.driver = driver
    
    def scraping_keys(self):
        """
        Set of dictionaries that define keys for scraping different sites.
        
        Returns
        -------
        None.
        
        """
        def Bloomberg():
            paragraph_reg = '<p>.*?</p>|<p class="paywall">.*?</p>|<h1 class=".*?">.*?</h1>|<li class="abstract-item.*?">.*?</li>'
            site_name     = 'Bloomberg'
            
            return dict(paragraph_reg = paragraph_reg, site_name = site_name)
        
        def Coindesk():
            paragraph_reg = '<p>.*?</p>|<b>.*?</b>|<p class=".*?">.*?</p>|' + \
                            '<p dir="ltr">.*?</p>|<h[1-3] class=".*?">.*?</h[1-3]>'
            site_name     = 'Coin Desk'
            
            return dict(paragraph_reg = paragraph_reg, site_name = site_name)
        
        def Forbes():
            paragraph_reg = '<p>.*?</p>|<p class=".*?">.*?</p>'
            site_name     = 'Forbes'
            
            return dict(paragraph_reg = paragraph_reg, site_name = site_name)
        
        def NYT():
            paragraph_reg = '<p>.*?</p>|<p class=".*?">.*?</p>'
            site_name     = 'NYT'
            
            return dict(paragraph_reg = paragraph_reg, site_name = site_name)
        
        def Reuters():
            paragraph_reg = '<p class=".*?" data-testid=".*?">.*?</p>|' + \
                            '<p class=".*?" .*?>.*?</p>|<p>.*?</p>|'
            site_name     = 'Reuters'
            
            return dict(paragraph_reg = paragraph_reg, site_name = site_name)
        
        def SeekingAlpha():
            # <li>.*?</li>|<li class=".*?">.*?</li>|
            paragraph_reg = '<p>.*?</p>|<h1 class=".*?" data-test-id="post-title">.*?</h1>|' + \
                            '<p class=".*?">.*?</p>'
            site_name     = 'Seeking Alpha'
            
            return dict(paragraph_reg = paragraph_reg, site_name = site_name)
        
        def Yahoo():
            paragraph_reg = [
                '<div class="caas-body">.*?</div>',
                '<p>.*?</p>|<p class=".*?">.*?</p>'  # |<header class=".*?">.*?</header>
            ]
            site_name     = 'Yahoo Finance'
            
            return dict(paragraph_reg = paragraph_reg, site_name = site_name)
        
        def WSJ():
            paragraph_reg = '<p>.*?</p>|<p class=".*?">.*?</p>|<p class=".*?" data-type="paragraph">.*?</p>'
            site_name     = 'WSJ'
            
            return dict(paragraph_reg = paragraph_reg, site_name = site_name)
        
        def Others():
            # Create a regular expression based on all the paragraph_reg variables defined
            # outside of this method
            regs = list()
            for re_dict in [
                    Bloomberg(), Coindesk(), Forbes(), NYT(), Reuters(), SeekingAlpha(), Yahoo(), WSJ()
            ]:
                par_reg = re_dict['paragraph_reg']
                par_reg = par_reg if type(par_reg) != list else par_reg[1]
                par_reg_items = par_reg.split('|')
                for reg in par_reg_items:
                    if reg not in regs and reg != '': regs.append(reg)
            paragraph_reg = '|'.join(regs)
            
            # paragraph_reg = '<p>.*?</p>|<p class=".*?">.*?</p>'
            site_name     = 'Unkown'
            
            return dict(paragraph_reg = paragraph_reg, site_name = site_name)
        
        return dict(
            bloomberg     = Bloomberg(),
            coindesk      = Coindesk(),
            forbes        = Forbes(),
            nytimes       = NYT(),
            reuters       = Reuters(),
            seekingalpha  = SeekingAlpha(),
            yahoo         = Yahoo(),
            wsj           = WSJ(),
            others        = Others()
        )
    
    def collect_articles(self):
        """
        Access the collected links and collect the article texts.
        
        Returns
        -------
        TYPE
            DESCRIPTION.
            
        """
        def read_article(page, pattern):
            """
            Collect article content from the page source and clean up the text.

            Parameters
            ----------
            page : str
                The full html string collected from the given article.
            pattern : str
                A regular expression of paragraph sections to find in the page.

            Returns
            -------
            sentences : list
                A nested list of strings containing the cleaned sentences with each word separated
                as it's own item in the nested list.

            """
            # Define search pattern
            paragraph_reg = pattern
            sub_reg1      = '<.*?>'
            sub_reg2      = 'Sign up for our newsletters|' + \
                            'Please consider using a different web browser for better experience.|' + \
                            'YOU MAY ALSO LIKE:.*|Tip:.*|Trending.*|' + \
                            '.*looking.*join us.*|.*current vacancies.*|' + \
                            'You should be aware of.*|' + \
                            'They may be used by those companies to build a profile of your.*|' + \
                            'They may be set by us or by third party providers.*|' + \
                            'Want the latest recommendations from.*\?|' + \
                            'Zacks’ free Fund Newsletter.*|' + \
                            'Privacy Policy|Cookie Policy|Terms and Conditions|This website is operated.*|' + \
                            'You should do your own.*?research before making any investment decisions.*|' + \
                            'Advertise(ment)|tap to bring up your browser menu.*|Ways to search.*' + \
                            '<span class="navi-bar.*?">.*?</span>'
            sub_reg3      = '&nbsp;|&amp;|  '
            
            # Create a list of month abbreviations to sub
            months = [month for index, month in enumerate(calendar.month_abbr)][1:]
            
            # Find article paragraphs in the page source
            if type(paragraph_reg) == list:
                # If a list of multiple regular expressions is passed,
                # collect paragraphs in multiple stages
                body_lst = re.findall(paragraph_reg[0], page)
                paragraph_lst = re.findall(paragraph_reg[1], '. '.join(body_lst))
            else:
                paragraph_lst = re.findall(paragraph_reg, page)
            
            # Clean up the articles for HTML elements
            cleaned_lst = []
            for p in paragraph_lst:
                p = re.sub('</li>|</h[1-9]>', '.', p).strip()
                p = re.sub(sub_reg1, '', p).strip()
                p = re.sub(sub_reg2, '', p).strip()
                p = re.sub(sub_reg3, ' ', p).strip()
                p = re.sub('"\.', '",,', p).strip()
                p = re.sub('U\.S\.|U.S.A', 'US', p).strip()
                p = re.sub('Mrs\.', 'Mrs', p).strip()
                p = re.sub('Mr\.', 'Mr', p).strip()
                p = re.sub('Ms\.', 'US', p).strip()
                p = re.sub('S P', 'S&P', p).strip()
                p = re.sub('No\.', 'Number', p).strip()
                
                for month in months:
                    p = re.sub(f'{month}\.', month, p).strip()
                
                # Store non-empty elements
                if p != '':
                    cleaned_lst.append(p)
                
            # Concat the cleaned article paragraphs
            article = ' '.join(cleaned_lst)
            # Break up block of text into a list of sentences
            sentences = article.split(". ")
            sentences = [s.strip() for s in sentences if len(s.strip()) > 0]
            sentences = [s + '.' if s[-1] != '.' else s for s in sentences]
            
            sentences_split = []
            for sentence in sentences:
                s = sentence.split(" ")
                sentences_split.append(s)
            
            return sentences_split
        
        ## Define a nested method for determining sentence similarity
        def sentence_similarity(sent1, sent2, stop_words=None):
            """
            Calculate a similarity score using the nltk cosine_distance function.
            
            Parameters
            ----------
            sent1 : lst
                A list of strings where each item is one word/term from a given sentence.
            sent2 : lst
                A list of strings where each item is one word/term from a given sentence.
                This list will be compared to the sent1.
            stop_words : lst, optional
                A list of stop words that should be ignored when calculating sentence similarity.
                The default is None.
                
            Returns
            -------
            float
                A score between 0 and 1 denoting the similarity between two sentences.
                A score of 0 means there is no similarity and 1 means they are the exact same.
                
            """
            # Define an empty list as a placeholder for stop words if no stop words were passed
            if stop_words is None: stop_words = []
            
            # Convert all words to lower case for more accurate comparisons
            sent1 = [w.lower() for w in sent1]
            sent2 = [w.lower() for w in sent2]
            
            # Create a list of all words
            all_words = list(set(sent1 + sent2))
            
            # Create two lists that are as long as the all_words list
            # vector1 corresponds to sent1 and vector2 to sent2
            # Default values for each item in the list will be 0
            # When each sent variable is iterated over and each word of the sentence is examined,
            # the value in the vector list that has the same position as the word in the all_words
            # list will be increased by 1.
            # For example, if the word `growth` is the third word in the sent1 list and `growth` is
            # also the fifth item in the all_words list, the fifth item in vector1 will be
            # increased by 1.
            vector1 = [0] * len(all_words)
            vector2 = [0] * len(all_words)
            
            # Build the vector for the first sentence
            for w in sent1:
                # Ignore stop_words
                if w in stop_words: continue
                # Increase the appropriate value in vector1 by 1
                vector1[all_words.index(w)] += 1
                
            # build the vector for the second sentence
            for w in sent2:
                # Ignore stop_words
                if w in stop_words: continue
                # Increase the appropriate value in vector2 by 1
                vector2[all_words.index(w)] += 1
            
            # Calculate and return the cosine similarity
            return 1 - cosine_distance(vector1, vector2)
        
        ## Define a nested method for building a similarity matrix
        def build_similarity_matrix(sentences, stop_words=None):
            """
            Create a similarity matrix of all sentences.
            
            Parameters
            ----------
            sentences : list
                A list of lists containing all sentences from an article where each nested
                list has each word as it's own item in the list.
            stop_words : list, optional
                A list of english stop words to be ignored when calculating similarity scores.
                The default is None.
                
            Returns
            -------
            similarity_matrix : np.array
                A numpy array containing the similarity scores of each sentence with
                all other sentences in an article.
            
            """
            # Create an empty similarity matrix
            similarity_matrix = np.zeros((len(sentences), len(sentences)))
            
            ## Iterate over each sentence
            for idx1 in range(len(sentences)):
                ## For each sentence, compare to all other sentences
                for idx2 in range(len(sentences)):
                    # TODO: Determine if this calculation should be excluded from the matrix
                    # Skip if both are same sentences
                    # if idx1 == idx2:
                    #     continue
                    
                    # Append similarity results storage matrix
                    similarity_matrix[idx1][idx2] = \
                        sentence_similarity(sentences[idx1], sentences[idx2], stop_words)
                        
            return similarity_matrix
        
        ## Define a nested method for generating `n` most relevant sentences
        def generate_summary(page, title, driver, top_n, read=True):
            """
            Generate a summary based on `top_n` most related sentences in the given article.
            
            This can be used to generate a summary of an individual article, or generate
            a summary of the article summaries in a corpus.
            
            In `summarize_articles` each article will first be processed to generate an article
            summary which is stored in a master list for all articles. The master list is then
            processed using this function as well to generate a summary of the article summaries.
            
            Parameters
            ----------
            page : list
                A nested list of the article sentences.
            title : str
                The article title.
            driver : TYPE
                DESCRIPTION.
            top_n : TYPE
                DESCRIPTION.
            read : TYPE, optional
                DESCRIPTION. The default is True.
            
            Returns
            -------
            str
                The summarized article text.
                
            """
            # Collect stopwords
            stop_words = nltk.corpus.stopwords.words("English")
            
            # # Read in the Loughran-MacDonald dictionaries for NLP in finance
            # LMcD_neg_url = 'https://raw.githubusercontent.com/AmeriFinn/NLP-Projects/main/LoughranMcDonald_Negative.csv'
            # LMcD_pos_url = 'https://raw.githubusercontent.com/AmeriFinn/NLP-Projects/main/LoughranMcDonald_Positive.csv'
            
            # LMcD_neg = list(pd.read_csv(LMcD_neg_url, index_col=0).index)
            # LMcD_pos = list(pd.read_csv(LMcD_pos_url, index_col=0).index)
            # LMcD_all = LMcD_neg + LMcD_pos
            # LMcD_kys = [1 for i in LMcD_all]
            # LMcD_col = {term: 1 for term in LMcD_all}
            
            ## Collect the page source for determining which scraping pattern to use
            try:
                source = driver.get_cookies()[0]['domain']
            except IndexError:
                try:
                    time.sleep(3)
                    source = driver.get_cookies()[0]['domain']
                except IndexError:
                    source = "www.others.com"
            except KeyError:
                source = "www.others.com"
            
            # Clean up the domain that was collected (or defaulted to)
            source = re.sub('//|www\.|\.c.(m){0,1}|\.', '', source).lower()
            source = 'coindesk' if source == 'indesk' else source
            
            # Determine which regular expression pattern should be used to find article text
            try:
                pattern = self.scraping_keys()[source]['paragraph_reg']
            except KeyError:
                pattern = self.scraping_keys()['others']['paragraph_reg']
                
            print('\n', source, pattern)
            
            # Read the page and tokenize
            if read:
                # We need to scrape the links to summarize those articles
                sentences = read_article(page, pattern)
                
                # If article text could not be found, notify user and return empty string
                if sentences == [['']]:
                    print(f"{title.upper()} - could not be collected")
                    return ''
            else:
                # We need to scrape the summarized articles
                sentences = page
            
            # Generate a similarity matrix across sentences
            sentence_similarity_martix = build_similarity_matrix(sentences, stop_words)
            
            # Rank the sentences in similarity matrix
            try:
                sentence_similarity_graph = nx.from_numpy_array(sentence_similarity_martix)
                scores = nx.pagerank_numpy(sentence_similarity_graph)
            except AttributeError:
                ## Try again with an updated page source
                # Read the page and tokenize
                if read:
                    # We need to scrape the links to summarize those articles
                    sentences = read_article(driver.page_source, pattern)
                    
                    # If article text could not be found, notify user and return empty string
                    if sentences == [['']]:
                        print(f"{title.upper()} - could not be collected")
                        return ''
                else:
                    # We need to scrape the summarized articles
                    sentences = page
                
                # Generate a similarity matrix across sentences
                sentence_similarity_martix = build_similarity_matrix(sentences, stop_words)
                try:
                    sentence_similarity_graph = nx.from_numpy_array(sentence_similarity_martix)
                    scores = nx.pagerank_numpy(sentence_similarity_graph)
                except AttributeError:
                    return ''
            
            # Sort the rank and pick top `n` sentences
            ranked_sentence = sorted(((scores[i], s) for i, s in enumerate(sentences)), reverse=True)
            
            # Join the list of words together into sentences
            summarize_text = []
            collect_n = len(ranked_sentence) if read else top_n
            for i in range(collect_n):
                if i <= len(ranked_sentence):
                    summarize_text.append(" ".join(ranked_sentence[i][1]))
                
            # Join the list of sentences together into a paragraph
            summarize_text = '. '.join(summarize_text)
            while '.. ' in summarize_text: summarize_text = summarize_text.replace('.. ', '. ')
            
            return summarize_text
        
        def summarize_articles(driver, top_n_df, index_df, top_n):
            """
            Summarize all of the articles in the corpus.
            
            Parameters
            ----------
            driver : selenium.webdriver
                The selenium driver object used to collect article texts.
            top_n_df : pd.DataFrame
                The article corpus reduced to the `top_n` most relevant articles.
            index_df : pd.DataFrame
                The entire article corpus.
            top_n : int
                The number of most relevant articles to scrape.
                
            Returns
            -------
            top_n_df : pd.DataFrame
                The article corpus reduced to the `top_n` most relevant articles.
            index_df : pd.DataFrame
                The entire article corpus.
            asset_summary : str
                The summary generated of all articles in the corpus containing the `n`
                most relevant articles.
                
            """
            ## Scrape and summarize the articles
            article_summaries = []
            for i, link in enumerate(top_n_df.Link):
                
                # Go to the link and collect entire HTML page source
                driver.get(link)
                time.sleep(1.5)
                try:
                    page = driver.page_source
                except (InvalidArgumentException, WebDriverException):
                    continue
                
                # Check if the article link needs to be updated
                url = driver.current_url
                # The only reason for the current_url to be different from link is if the browser
                # was redirected
                if url != link:
                    index_df.loc[i, 'Link'] = url
                    
                # Check if the article title needs to be updated
                title = driver.title
                if (str(title) != '') & (title != index_df.loc[i, 'Title']):
                    index_df.loc[i, 'Title'] = title
                    
                # Check if the source/publisher needs to be updated
                if index_df.loc[i, 'Source'] == 'Google':
                    try:
                        # Try to collect a better source/publisher name
                        source = driver.get_cookies()[0]['domain']
                        source = re.sub('//|www\.|\.c.(m){0,1}|\\.', '', source).title()
                        source = re.sub('Marketwatch', 'Market Watch', source)
                        source = re.sub('Wsj', 'WSJ', source)
                        source = re.sub('Nytimes', 'NYT', source)
                        source = re.sub('Bitcoin', 'Bitcoin.com', source)
                        
                        if source.strip() != '':
                            index_df.loc[i, 'Source'] = source
                    
                    except IndexError:
                        try:
                            source = re.search('//(www){0,1}(\.){0,1}.*?\.c.(m){0,1}', url).group(0)
                            source = re.sub('//|www.|.c.(m){0,1}|\\.', '', source).title()
                            source = re.sub('Marketwatch', 'Market Watch', source)
                            source = re.sub('Wsj', 'WSJ', source)
                            source = re.sub('Nytimes', 'NYT', source)
                            source = re.sub('Bitcoin', 'Bitcoin.com', source)
                            
                            if source.strip() != '':
                                index_df.loc[i, 'Source'] = source
                                
                        except AttributeError:
                            print(f'Could not collect a better source name for {title}')
                            
                # Generate a 5 sentence summary of the article and store results
                summ_page = generate_summary(page, driver.title, driver, top_n)
                article_summaries.append(summ_page)
                
                # Clean up the article summary a bit
                # summ_page = re.sub('\n|[^a-z\s]|\s[a-z]\s', ' ', summ_page).strip()
                while '  ' in summ_page: summ_page = summ_page.replace('  ', ' ')
                summ_page = re.sub('\s[a-z]\s', ' ', summ_page).strip()
                
                # Create the TextBlob object and collect sentiment and objectivity scores
                blob = TextBlob(summ_page)
                polar = round(blob.sentiment.polarity * 100, 2)
                sbjct = round(blob.sentiment.subjectivity * 100, 2)
                
                # Assign the polarity and subjectivity/objectivity scores
                index_df.loc[i, 'Polarity'] = polar
                index_df.loc[i, 'Subjectivity'] = sbjct
                
                print(f"{round(100 * i / 15, 2)}% | Summarized article | {driver.title}\n")
                                        
            ## Concat the article summaries to then summarize the article summaries
            asset_summary = ' '.join(article_summaries)
            
            # Split up the article summary into a list of strings/sentences
            sentences = asset_summary.split(". ")
            sentences = [s.strip() for s in sentences if len(s.strip()) > 0]
            sentences = [s + '.' if s[-1] != '.' else s for s in sentences]
            
            # Then split up the sentences into a list with each word being its own item in the list
            sentences_split = []
            for sentence in sentences:
                s = sentence.split(" ")
                sentences_split.append(s)
            
            # Create the summary for all articles used to encapsulate the common theme(s) of the day
            asset_summary = generate_summary(sentences_split, None, driver, top_n=15, read=False)
            
            return top_n_df, index_df, asset_summary
        
        ## Collect the index df and driver for scraping top 10 articles
        index_df = self.index_df
        driver   = self.driver
        top_n    = self.top_n
        
        ## Subset top `n` links based on relevance score.
        top_n_df = index_df.loc[:top_n, ['Source', 'Title', 'Link']]
        
        top_n_df, index_df, asset_summary = summarize_articles(driver, top_n_df, index_df, top_n)
        
        self.top_n_df      = top_n_df
        self.index_df      = index_df
        self.asset_summary = asset_summary
        
        # Close the driver if necessary
        if self.close_driver: driver.quit()
            
        self.driver = driver
        
    def go(self):
        """Execute the sole method of this class."""
        self.collect_articles()
        
# asset_class, topic = 'EQUITY', '^GSPC'
# # it = index_topic(asset_class, topic)
# # it.go()

# # it.source_articles['google']
# # it.index_df

# # self = it
# # self.driver.get(it.index_df.Link.iloc[-3])

# si = score_index(asset_class, topic)
# si.go()

# si.index_df
# si.index_df.to_csv('test.csv')

# test = si.index_df.loc[:,
#                 ['LMcD_Neg_Terms',  'LMcD_Pos_Terms',  'LMcD_Tot_Terms',
#                   'Date_Relevance',  'Title_Relevance', 'Relevancy_Score',
#                   'Date', 'Title', 'Source', 'Link']]

# self = si

# sa = summarize_articles(asset_class, topic)
# sa.go()

# print(sa.asset_summary)
# sa.index_df.Link[:15]
