# -*- coding: utf-8 -*-
"""
Created on Tue Aug 23 21:17:35 2022.

Initialize the selenium browser object that will be used to scrape news articles.

@author: grega
"""
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException

def init_browser():
    """
    Initialize a selenium webdriver and log in to a variety of news sources that have paywalls.
    
    Currently, the following news outlets will be logged in to:
        - The Wall Street Journal
        - The New York Times
        - Bloomberg
        - Seeking Alpha
    
    Returns
    -------
    driver : selenium.webdriver
        A selenium webdriver object that has logged into a variety of news sources.

    """
    ## Initiate `Firefox` browser to be used in my_weekly_article module.
    fp = webdriver.FirefoxProfile()
    
    ## Open the browser and go to the desired news page to scrape.
    driver = webdriver.Firefox(firefox_profile=fp)
    driver.maximize_window()
    
    ## Log in to WSJ
    wsj_login = os.environ.get('WSJ_Login').split('|')
    username = wsj_login[0]
    password = wsj_login[1]
    print(f'Username: {username}\nPassword: {password}')
    driver.get("https://www.wsj.com/login")
    
    try:
        driver.find_element_by_id('username').send_keys(username)
        driver.find_element_by_id('password').send_keys(password)
        driver.find_element(By.XPATH, '//button').click()
    except (NoSuchElementException, ElementNotInteractableException):
        print('Need to manually enter login info')
        
    input('Logged in to WSJ?')
    
    ## Log in to NYT
    nyt_login = os.environ.get('NYT_Login').split('|')
    username = nyt_login[0]
    password = nyt_login[1]
    print(f'Username: {username}\nPassword: {password}')
    
    try:
        driver.get("https://www.nytimes.com/login")
        time.sleep(1)
        driver.find_element_by_id('username').send_keys(username)
    except (NoSuchElementException, ElementNotInteractableException):
        try:
            driver.find_element_by_id('email').send_keys(username)
            driver.find_element(By.XPATH, '//button[text()="Continue"]').click()
        except (NoSuchElementException, ElementNotInteractableException):
            print('Need to manually enter login info')
        
    try:
        driver.find_element_by_id('password').send_keys(password)
        driver.find_element(By.XPATH, '//button').click()
    except (NoSuchElementException, ElementNotInteractableException):
        print('Need to manually enter login info')
    
    input('Logged in to NYT?')
    
    ## Log in to Bloomberg
    bloom_login = os.environ.get('Bloomberg_Login').split('|')
    username = bloom_login[0]
    password = bloom_login[1]
    print(f'Username: {username}\nPassword: {password}')
    driver.get("https://www.bloomberg.com/account/signin")
    time.sleep(1)
    try:
        driver.find_element_by_name('').send_keys(username)
        driver.find_element_by_name('password').send_keys(password)
        driver.find_element(By.XPATH, '//button[text()="Sign in"]').click()
    except (NoSuchElementException, ElementNotInteractableException):
        print('Need to manually log in!!!')
    input('Logged in to Bloomberg?')
    
    # Log in to Seeking Alpha
    seek_login = os.environ.get('SeekingAlpha_Login').split('|')
    username = seek_login[0]
    password = seek_login[1]
    print(f'Username: {username}\nPassword: {password}')
    
    try:
        driver.get("https://www.seekingalpha.com/login")
        time.sleep(1)
        driver.find_element_by_name('email').send_keys(username)
        driver.find_element_by_name('password').send_keys(password)
    except (NoSuchElementException, ElementNotInteractableException):
        print('Need to manually log in!!!')
    
    input('Logged in to Seeking Alpha?')
    
    return driver

# driver = init_browser()
