# -*- coding: utf-8 -*-
"""all_in_one.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1-ZB_ZkaJcYGfRheHWzvw1-srNpmC6ElY

Google Scholar Research Papers Scraper

This script scrapes Google Scholar profiles for author and article information.Then it classifies the articles as "sustainable" or not and then further classifies the articles with various pre-defined sustainability themes using the OpenAI API.
The data is then cleaned and processed into a structured format.
"
"""

# import the necessary packages
# import the scraping related packages
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.proxy import Proxy, ProxyType
from bs4 import BeautifulSoup
import re
# import the data processing related packages
import pandas as pd
# import the system related packages
import sys
import os
import time
import logging
import gspread
import warnings
import tqdm
warnings.filterwarnings("ignore", category=DeprecationWarning)
from tqdm.notebook import tqdm
# import the google sheets related packages
from oauth2client.service_account import ServiceAccountCredentials
# import the openai
import openai
import timestamp

"""#### Block 1:
Take the "First Name", "Last Name", "University" from the Googlesheet "researchers" master table directly and scrap the researcher's URL
"""

def scrape_google_scholar_profile(first_name, last_name, institution, is_professor):
    """
        Scrapes the Google Scholar profile for a researcher.

        Args:
            first_name (str): The first name of the researcher.
            last_name (str): The last name of the researcher.
            institution (str): The institution of the researcher.
            is_professor (bool): Whether the researcher is a professor.

        Returns:
            dict: A dictionary containing the profile URL, author ID, and other details, or an error message.
    """
    print ("==================== Task 1: Scraping Google Scholar Profile  ====================")
    try:
        # the googlesheet captures the title of a professor in their insititutions, only capture the google sholar profile for professors can effectively short listed the reserachers need to be scrapped
        if "professor" in is_professor.lower():
            # remove special characters from the names and institution so the url won't break due to these and didn't use the full parameter to search the researcher
            first_name = first_name.replace("'", "").replace("-", " ").replace(" ", "").strip()
            last_name = last_name.replace("'", "").replace("-", " ").replace(" ", "").strip()
            institution = institution.replace("'", "").replace("-", " ").replace(" ", "").strip()

            # set up the selenium webdriver, default code, don't change
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--disable-gpu')
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

            # assemble the URL to mimic the manual search of the researcher
            researcher_search_url = f"https://scholar.google.com/citations?hl=en&view_op=search_authors&mauthors={first_name}+{last_name}+{institution}"

            # visit the webpage, to help with the weak internet at school, try max 3 times to load the page if it fails
            for attempt in range(3):
                try:
                    driver.get(researcher_search_url)
                    print(f"Attempt {attempt + 1} to load for {first_name} {last_name} at {institution}")
                    break
                except Exception as e:
                    print(f"Attempt {attempt + 1} to load for {first_name} {last_name} at {institution}")
                    time.sleep(2)
            else:
                print(f"Failed to load {first_name} {last_name} at {institution} after 3 attempts.")
                return None

            # wait for the page to load
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))

            # Get the page source
            page_source = driver.page_source

            # Parse the HTML with BeautifulSoup
            soup = BeautifulSoup(page_source, 'html.parser')

            # Check if the page has a CAPTCHA
            if "captcha-form" in driver.page_source:
                driver.quit()
                print("CAPTCHA detected. Please solve the CAPTCHA manually.")
                google_scholar_url = {
                    'author_id' : "",
                    'first_name' : first_name,
                    'last_name': last_name,
                    'institution': institution,
                    'is_professor': "Y",
                    'researcher_google_scholar_url': "CAPTCHA detected"
                }
                return google_scholar_url

            # Find all profile links, if only profile found, take that, if more than one, take the first one, if none, return no profile found
            profile_links = soup.find_all('a', class_='gs_ai_pho')
            if len(profile_links) == 1:
                profile_url = profile_links[0]['href']
                researcher_url = f"https://scholar.google.com{profile_url}"
                driver.quit()
                print(f'obtained the researcher url: {researcher_url}')
                author_id = re.search(r'user=([^&]+)', researcher_url).group(1)
                google_scholar_url = {
                    'author_id' : author_id,
                    'first_name' : first_name,
                    'last_name': last_name,
                    'institution': institution,
                    'is_professor': "Y",
                    'researcher_google_scholar_url': researcher_url
                }
                return google_scholar_url
            elif len(profile_links) > 1:
                profile_url = profile_links[0]['href']
                researcher_url = f"https://scholar.google.com{profile_url}"
                driver.quit()
                print(f'More than one profile found, took the first profile: {researcher_url}')
                author_id = re.search(r'user=([^&]+)', researcher_url).group(1)
                google_scholar_url = {
                    'author_id' : author_id,
                    'first_name' : first_name,
                    'last_name': last_name,
                    'institution': institution,
                    'is_professor': "Y",
                    'researcher_google_scholar_url': researcher_url
                }
                return google_scholar_url
            else:
                driver.quit()
                google_scholar_url = {
                    'author_id' : "",
                    'first_name' : first_name,
                    'last_name': last_name,
                    'institution': institution,
                    'is_professor': "Y",
                    'researcher_google_scholar_url': "No profile found"
                }
                return google_scholar_url
        else:
            google_scholar_url = {
                'author_id' : "",
                'first_name' : first_name,
                'last_name': last_name,
                'institution': institution,
                'is_professor': "N",
                'researcher_google_scholar_url': "Not a professor"
            }
            return google_scholar_url

    except Exception as e:
        driver.quit()
        return f"Error: {e}"

# # Example usage
# first_name = "Juan"
# last_name = "Serpa"
# # first_name = "Javad"
# # last_name = "Nasiry"
# institution = "McGill University"
# is_professor = "Associate Professor"
# researcher_google_scholar_url = scrape_google_scholar_profile(first_name, last_name, institution, is_professor)
# researcher_google_scholar_url = researcher_google_scholar_url["researcher_google_scholar_url"]

"""#### Block 2:
Take the researcher's google scholar profile url to scrap all the papers within this author's profile page
"""

def scrape_articles_from_profile(researcher_google_scholar_url):
    """
    Scrapes all articles listed in a researcher's Google Scholar profile.

    Args:
        researcher_google_scholar_url (str): The URL of the researcher's Google Scholar profile.

    Returns:
        list: A list of dictionaries with details such as title, link, and publication year for each article.
    """
    print ("==================== Task 2: Scraping All Articles List from Google Scholar Profile  ====================")
    try:
        # Set up the Selenium driver
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

        # Visit the researcher's profile, for max 3 times to load the page if it fails
        for attempt in range(3):
            try:
                driver.get(researcher_google_scholar_url)
                break
            except Exception as e:
                print(f"Attempt {attempt + 1} failed for {researcher_google_scholar_url}: {e}")
                time.sleep(2)
        else:
            print(f"Failed to load {researcher_google_scholar_url} after 3 attempts.")
            return None

        # Click the "show more" button until it disappears to scroll through all articles
        while True:
            try:
                show_more_button = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, 'gsc_bpf_more'))
                )
                if show_more_button.is_displayed() and show_more_button.is_enabled():
                    show_more_button.click()
                    WebDriverWait(driver, 10).until_not(EC.element_to_be_clickable((By.ID, 'gsc_bpf_more')))
                    time.sleep(1)
                else:
                    break
            except (EC.TimeoutException, EC.NoSuchElementException) as e:
                print(f"An error occurred: {e}")
                break
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
                break

        # Get the page source
        page_source = driver.page_source

        # Parse the HTML with BeautifulSoup
        soup = BeautifulSoup(page_source, 'html.parser')

        if "captcha-form" in driver.page_source:
            driver.quit()
            print("CAPTCHA detected. Please solve the CAPTCHA manually.")
            return None

        # Find all article links and titles
        articles = soup.find_all('tr', {'class': 'gsc_a_tr'})

        data = []

        # Extract each article's title, link, and year
        for article in articles:
            title_tag = article.find('a', {'class': 'gsc_a_at'})
            if title_tag:
                title = title_tag.text
                link = "https://scholar.google.com" + title_tag['href']
                year_element = article.find('span', {'class': 'gsc_a_h'})
                year = year_element.text if year_element else "Year not available"
                data.append({
                    'researcher_google_scholar_url': researcher_google_scholar_url,
                    'research_paper_title': title,
                    'article_google_scholar_url': link,
                    'research_paper_publication_year': year
                })

        driver.quit()
        # return the first 100 articles, if more than 100, only return the first 100
        return data[:100]

    except Exception as e:
        driver.quit()
        return f"Error: {e}"

# # Example usage
# articles = scrape_articles_from_profile(researcher_google_scholar_url)
# profile_article_list = pd.DataFrame(articles)
# profile_article_list

"""#### Block 3:
Loop the article list, use the article google scholar url to go to the article detail page and scrap the attributes from it
"""

def extract_article_details(article_google_scholar_url, research_paper_publication_year,author_id):
    """
    Scrapes all articles listed in a researcher's Google Scholar profile. Extract one arcticle at a time.

    Args:
        researcher_google_scholar_url (str): The URL of the researcher's Google Scholar profile.

    Returns:
        list: A list of dictionaries with details such as title, link, and publication year for each article.

    """
    print ("==================== Task 3: Scraping Details for All the Articles ====================")
    try:
        # Set up the Selenium driver
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

        # Visit the webpage
        for attempt in range(3):
            try:
                driver.get(article_google_scholar_url)
                print(f"Attempt {attempt + 1} to load {article_google_scholar_url}")
                break
            except Exception as e:
                print(f"Attempt {attempt + 1} failed for {article_google_scholar_url}: {e}")
                time.sleep(2)
        else:
            print(f"Failed to load {article_google_scholar_url} after 3 attempts.")
            return None

        # Get the page source
        page_source = driver.page_source

        # Parse the HTML with BeautifulSoup
        soup = BeautifulSoup(page_source, 'html.parser')

        # Print message if CAPTCHA is detected
        if "captcha-form" in driver.page_source:
            driver.quit()
            print("CAPTCHA detected. Please solve the CAPTCHA manually.")
            return None

        # Extract article details with checks, since these information are under the same class, we can use the same function to extract them
        def get_value(field_name):
            field = soup.find('div', text=field_name)
            if field:
                value = field.find_next_sibling('div', {'class': 'gsc_oci_value'})
                return value.text.strip() if value else 'N/A'
            return None

        def get_citations():
            citations_tag = soup.find('a', href=re.compile(r'.*cites=.*'))
            if citations_tag:
                match = re.search(r'Cited by (\d+)', citations_tag.text)
                return match.group(1) if match else 'N/A'
            return None

        title_tag = soup.find('a', {'class': 'gsc_oci_title_link'})
        # if the title doesn't have a link, then use the title from the snippet
        if title_tag is None:
            title_tag = soup.find('div', {'id': 'gsc_oci_title'})
        snippet_tag = soup.find('div', {'class': 'gsc_oci_merged_snippet'})
        link_tag = snippet_tag.find('a') if snippet_tag else None

        # Extract the article ID from the "Related Article" link at the bottom of the page
        # try three times to load the article, if failed, return None
        article_id = None
        for attempt in range(3):
            if article_id is None:
                try:
                    article_id_link = soup.find_all('a', class_='gsc_oms_link')
                    for link in article_id_link:
                        if 'related' in link.text.lower():
                            article_id = link['href'].split('related:')[1].split(':')[0]
                            break
                except Exception as e:
                    print(f"Attempt {attempt + 1} failed to extract article ID: {e}")
                    time.sleep(2)
            else:
                break

        # one article's details will be stored in this dictionary
        article_details = {
            'research_paper_title': title_tag.text.strip() if title_tag else 'N/A',
            'article_google_scholar_url': article_google_scholar_url,
            'researcher_paper_url': "https://scholar.google.com" + link_tag['href'] if link_tag else 'N/A',
            'journal_name': get_value('Journal'),
            'researcher_paper_publication_year': research_paper_publication_year,
            'journal_issue': get_value('Issue'),
            'journal_volume': get_value('Volume'),
            'journal_pages': get_value('Pages'),
            'abstract': get_value('Description'),
            'citation_count': get_citations(),
            'publisher': get_value('Publisher'),
            'authors': get_value('Authors'),
            'publication_date': get_value('Publication date'),
            'author_id': author_id,
            'article_id': article_id
        }
        print("----------------- Load Successful, Extracting the Details -----------------")

        # tag working papers, if 0 then it is a working paper, the keywords list can be updated to include more keywords, if journal name, abstract or publisher contains the keywords, then it is a working paper
        keywords = ['SSRN', 'working paper', 'revision', 'review']
        journal_name = str(article_details['journal_name']).lower()
        abstract = str(article_details['abstract']).lower()
        publisher = str(article_details['publisher']).lower()
        # Initialize the status to 1 (default)
        article_details["research_paper_status"] = 1

        for keyword in keywords:
            if keyword.lower() in journal_name or keyword.lower() in abstract or keyword.lower() in publisher:
                article_details["research_paper_status"] = 0
                break  # Exit the loop as we have found a matching keyword

        print(f"Extracted details for {article_google_scholar_url}")
        driver.quit()
        return article_details

    except Exception as e:
        driver.quit()
        return f"Error: {e}"

# # Example usage
# article_google_scholar_url = profile_article_list["article_google_scholar_url"][5]
# research_paper_publication_year = profile_article_list["research_paper_publication_year"][5]
# author_id = re.search(r'user=([^&]+)', researcher_google_scholar_url).group(1)
# article_details = extract_article_details(article_google_scholar_url, research_paper_publication_year,author_id)
# article_details = pd.DataFrame([article_details])
# article_details.head()

"""### Block 4:
Take the scrapped article lists' title and abstract, use them to classify the paper, so the Sustainable paper could be identified
"""

# # Plug in the OpenAI API key
# openai.api_key = 'sk-proj-ND2odcQXpiPBmp5oqN3nT3BlbkFJrSSH81a8XOZvtz9sBHF4'
# # Read the theme from the Google Sheet
# # Define the scope
# scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# # Obtain the service account credentials from the JSON file, which is downloaded from the Google Cloud Platform from Addison's account
# json_key_file = "researchdb-464d2570e016.json"

# # Give everything needed to access a specific worksheet within a Google Sheet
# # Input: Google Sheet URL and the name of the worksheet
# google_sheet_url = "https://docs.google.com/spreadsheets/d/1NT-M4huHXU9nh63DxuM79m8h4ihC3de-vjuq9g1CIkE/edit?gid=888944986#gid=888944986"
# worksheet_name = "themes"

# # Add credentials to the account
# #creds = ServiceAccountCredentials.from_json_keyfile_name(f'{path_json_key}+{json_key_file}', scope)
# creds = ServiceAccountCredentials.from_json_keyfile_name(json_key_file, scope)

# # Authorize the client
# client = gspread.authorize(creds)
# print(client)

# # Open the shared Google Sheet by its URL
# # Open the worksheet for the input
# preadsheet = client.open_by_url(google_sheet_url)
# worksheet = preadsheet.worksheet(worksheet_name)

# # Read data from the worksheet
# input_data = worksheet.get_all_records()
# themes = pd.DataFrame(input_data)
# subthemes = themes['subtheme'].tolist()

def classify_paper(title, abstract,subthemes):
    """
    Classifies a paper as sustainability-related or not using the OpenAI API.

    Args:
        title (str): The title of the paper.
        abstract (str): The abstract of the paper.

    Returns:
        tuple: A tuple containing the classification result and the detected language.
    """
    print("----------------- Identify the Sustainable Papers From All Articles List and Classify the Theme:Subtheme -----------------")
    prompt = (
        f"Use the Title: {title}\n and the Abstract: {abstract}\n\n of a paper to firstly to decide if the paper is about sustainability, if the paper is not about sustainability, return 'Exclude: Not a sustainability paper'."
        f"If the paper is about sustainability, based on the themes: {subthemes}, classify this paper. One paper can only have one theme. "
        "Please return the exact theme from the list without adding any additional words and no quotes. "
        "If it does not clearly fall into any theme or if there is any ambiguity, return 'Exclude: Not a sustainability paper', please be very closed mind on this, we need paper that is obviously related to sustainability. "
        "If there is not sufficient data for you to perform the task, return 'Exclude: Not sufficient data'. "
        f"Must detect the language used in the {title} and {abstract}, e.g. English, Spanish, etc. If not able to detect, return 'Language not detected'.\n\n"
        "Return the response in the following format: \n"
        "Classification;Theme\n"
        "Language;Language"
    )

    max_attempts = 4
    attempts = 0

    while attempts < max_attempts:
        print(f"Attempt {attempts + 1} to classify the {title} paper")
        try:
            # plug in the model, code can be found in the openai API doc
            response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            )
            # Extract the response content
            response_content = response.choices[0].message.content.strip()

            try:
                classification, language = response_content.split('\n')
                classification = classification.split(';')[1]
                language = language.split(';')[1]

                print(f"Successfully classified the paper as: {classification}")
                return classification, language
                break  # Break the loop if successful

            except Exception as e:
                attempts += 1
                if attempts >= max_attempts:
                    print(f"Error parsing response: {e}")
                    return "Exclude: Error parsing response", str(e)

        except Exception as api_error:
            attempts += 1
            if attempts >= max_attempts:
                print(f"Error calling OpenAI API: {api_error}")
                return "Exclude: Error calling OpenAI API", str(api_error)

    print(f"Failed to classify the paper after {max_attempts} attempts")
    return "Exclude: Error", "Unknown"

# # Example usage
# result = classify_paper(article_details["research_paper_title"], article_details["abstract"])
# article_details["article_theme"] = result[0]
# article_details["language"] = result[1]

"""### Block 5:
For papers which are classified as a sustainable paper, take the title of it, through it into the Google Scholar Search under the "Article" tab to grab the author's profile for all the authors
"""

def extract_author_details(research_paper_title, article_google_scholar_url):
    """
    Extracts author details from a Google Scholar article.

    Args:
        research_paper_title (str): The title of the research paper.
        article_google_scholar_url (str): The URL of the article on Google Scholar.

    Returns:
        list: A list of dictionaries containing author details such as name, URL, and ID.
    """
    print("----------------- Extracting All Author Profiles From Article Search Bar -----------------")
    try:
        # Clean the input data
        query = research_paper_title.replace(" ", "+").strip()

        if not query:
            print("Skipping as query is empty")
            return None

        print(f"Processing article with query: {query}")

        # Set up the Selenium driver
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        print("Driver is ready")

        article_search_url = f"https://scholar.google.com/scholar?hl=en&as_sdt=0%2C5&q={query}&btnG="

        # Visit the webpage
        for attempt in range(3):
            try:
                driver.get(article_search_url)
                print(f"Attempt {attempt + 1} to load author details for {article_search_url}")
                break
            except Exception as e:
                print(f"Attempt {attempt + 1} failed for loading author details for {article_search_url}: {e}")
                time.sleep(2)
        else:
            print(f"Failed to load {article_search_url} after 3 attempts.")
            return None

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
        print(f"Visiting URL: {article_search_url}")

        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        if "captcha-form" in driver.page_source:
            print("CAPTCHA detected. Please solve the CAPTCHA manually and press Enter to continue...")
            driver.quit()
            return "CAPTCHA"

        final_data = []
        # Get the first article from the search result because it is the most relevant, if the first article is not found, return None
        article = soup.find_all('h3', class_='gs_rt')[0]


        if article:
            article_url = ""
            article_id = article.find('a')['id'] if article.find('a') and 'id' in article.find('a').attrs else None
            if article.find('a'):
                article_url = article.find('a')['href']

            authors = article.find_next('div', class_='gs_a')
            author_links = authors.find_all('a')
            author_names = authors.text.split("-")[0].split(",")

            for a in author_links:
                author_url = f"https://scholar.google.com{a['href']}"
                author_name = a.text.strip()
                author_id = re.search(r'user=([^&]+)', author_url).group(1)

                # Visit author's profile to get the full name
                driver.get(author_url)
                profile_soup = BeautifulSoup(driver.page_source, 'html.parser')
                full_name = profile_soup.find('div', id='gsc_prf_in').text if profile_soup.find('div', id='gsc_prf_in') else author_name

                final_data.append({
                    'article_google_scholar_url' : article_google_scholar_url,
                    'research_paper_title': research_paper_title,
                    'research_paper_url': article_url,
                    'author_name': full_name,
                    'author_url': author_url,
                    'author_id': author_id,
                    'article_id': article_id
                })

            # For authors without profile links, just capture their names
            for other_author in author_names:
                if other_author.strip() not in [a.text.strip() for a in author_links]:
                    other_author = other_author.strip()
                    print(f"Author: {other_author}")

                    final_data.append({
                        'article_google_scholar_url' : article_google_scholar_url,
                        'research_paper_title': research_paper_title,
                        'research_paper_url': article_url,
                        'author_name': other_author,
                        'author_url': None,
                        'author_id': None,
                        'article_id': article_id
                    })

            print(f"Obtained the author details for {research_paper_title}")
        else:
            final_data.append({
                'article_google_scholar_url' : article_google_scholar_url,
                'research_paper_title': research_paper_title,
                'research_paper_url': "No article found",
                'author_name': None,
                'author_url': None,
                'author_id': None,
                'article_id': None
            })
            print(f"No article found for {research_paper_title}")

        driver.quit()
        return final_data

    except Exception as e:
        print(f"Error: {e}")
        driver.quit()
        return None

# # Example usage
# research_paper_title = article_details['research_paper_title'].values[0]
# article_google_scholar_url = article_details['article_google_scholar_url'].values[0]
# author_details = extract_author_details(research_paper_title, article_google_scholar_url)
# author_details = pd.DataFrame(author_details)
# author_details.head()

"""### Block 6:
Cleanse the junction and the article table get from the result

Need to figure out how to: detect the article that has no primary author in the author list
Need to extract robost primary key for both article and authors
"""

def clean_and_merge_data(article_details, author_details):
    """
    Cleans and merges article and author data.

    Args:
        article_details (pd.DataFrame): A DataFrame containing article details.
        author_details (pd.DataFrame): A DataFrame containing author details.

    Returns:
        tuple: A tuple containing cleaned article and author tables.
    """
    print ("==================== Task 4: Cleaning and Merging the Data ====================")
    # merge the two tables so only the articles from the primary researcher's profile and the primary researcher's name are included
    # so both table only have the rows that are relevant to the primary researcher
    article_table = pd.merge(article_details, author_details[["article_id", "author_id"]], on=['article_id', 'author_id'], how='inner').drop_duplicates()
    author_table = pd.merge(author_details, article_table[["article_id"]], on='article_id', how='inner').drop_duplicates()
    article_table = article_table[['article_id', 'research_paper_title', 'article_google_scholar_url', 'researcher_paper_url', 'journal_name',
                                   'researcher_paper_publication_year', 'journal_issue', 'journal_volume', 'journal_pages', 'article_theme', 'abstract', 'citation_count',
                                   'research_paper_status', 'language', 'author_id']]
    # select the columns to be included in the author table
    # split the author full name into first name and last name, with the first letter capitalized
    # last name is the last word after the last space
    author_table['last_name'] = author_table['author_name'].apply(lambda x: x.split()[-1].capitalize()).str.strip()
    # first name is the full name without the last name
    author_table['first_name'] = author_table['author_name'].apply(lambda x: ' '.join(x.split()[:-1]).capitalize()).str.strip()
    # rank the authors based on the order of appearance in the article for one article
    author_table['rank'] = author_table.groupby('article_id').cumcount() + 1
    # change column name author_url to researcher_google_scholar_url
    author_table.rename(columns={'author_url': 'researcher_google_scholar_url'}, inplace=True)
    # select the columns to be included in the author table
    author_table = author_table[['article_id', 'author_id', 'rank', 'last_name', 'first_name', 'researcher_google_scholar_url']]
    return article_table, author_table

def main():
    """
    Main function that orchestrates the process of scraping Google Scholar profiles, extracting articles and author details,
    classifying articles, and saving the data to an Excel file.
    """
    user_name = "Addison"
    #openai.api_key = 'sk-proj-ND2odcQXpiPBmp5oqN3nT3BlbkFJrSSH81a8XOZvtz9sBHF4'
    # # User-specified row range
    # start_row = 0  # Change this to the desired start row (0-indexed)
    # end_row = None  # Change this to the desired end row (exclusive), or leave as None to process all rows

    # # Read the first name, last name, and institution from the Google Sheet
    print("==================================== Start the Scrapper: Read Data From Google Sheet ====================================")
    # Define the scope
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

    # Obtain the service account credentials from the JSON file, which need to be saved in the same directory as the script
    json_key_file = "researchdb-464d2570e016.json"
    #json_key_file="/content/drive/MyDrive/temporary_files/Codes/codes_in_knitting/researchdb-464d2570e016.json"
    # # Give everything needed to access a specific worksheet within a Google Sheet
    # # Input: Google Sheet URL and the name of the worksheet
    # master_sheet_url = "https://docs.google.com/spreadsheets/d/1NT-M4huHXU9nh63DxuM79m8h4ihC3de-vjuq9g1CIkE/edit?gid=888944986#gid=888944986"
    # worksheet_name = "researchers"

    # Add credentials to the account
    creds = ServiceAccountCredentials.from_json_keyfile_name(json_key_file, scope)

    # Authorize the client
    client = gspread.authorize(creds)

    # # Open the shared Google Sheet by its URL
    # spreadsheet = client.open_by_url(master_sheet_url)
    # worksheet = spreadsheet.worksheet(worksheet_name)

    # input_data = worksheet.get_all_records()

    # # Slice the data according to the specified row range
    # input_data = input_data[start_row:end_row]


    # Give everything needed to access a specific worksheet within a Google Sheet
    # Input: Google Sheet URL and the name of the worksheet
    google_sheet_url = "https://docs.google.com/spreadsheets/d/1NT-M4huHXU9nh63DxuM79m8h4ihC3de-vjuq9g1CIkE/edit?gid=888944986#gid=888944986"
    worksheet_name = "themes"

    # Open the shared Google Sheet by its URL
    # Open the worksheet for the input
    preadsheet = client.open_by_url(google_sheet_url)
    worksheet = preadsheet.worksheet(worksheet_name)

    # Read data from the worksheet
    input_data = worksheet.get_all_records()
    themes = pd.DataFrame(input_data)
    subthemes = themes['subtheme'].tolist()

    # test example, use Juan Serpa as the test example
    input_data = input_data = [{'first_name': 'Juan', 'last_name': 'Serpa', 'researcher_university': 'McGill University', 'position_institute': 'Professor'},{'first_name': 'Javad', 'last_name': 'Nasiry', 'researcher_university': 'McGill University', 'position_institute': 'Professor'}]
    #input_data = input_data = [{'first_name': 'Juan', 'last_name': 'Serpa', 'researcher_university': 'McGill University', 'position_institute': 'Professor'}]

    researchers = pd.DataFrame(input_data)
    all_google_scholar_urls = []
    all_article_details = []
    sus_article_details = []
    sus_author_details = []

    for _, researcher in researchers.iterrows():
        # Proceeding with the google scholar url
        first_name = researcher['first_name']
        last_name = researcher['last_name']
        institution = researcher['researcher_university']
        is_professor = researcher['position_institute']
        # Save the scrapped Google Scholar URLs
        researcher_url = scrape_google_scholar_profile(first_name, last_name, institution, is_professor)
        all_google_scholar_urls.append(researcher_url)

        # Proceeding with the article
        researcher_google_scholar_url = researcher_url["researcher_google_scholar_url"]
        author_id = researcher_url["author_id"]

        if researcher_google_scholar_url and "http" in researcher_google_scholar_url:
            articles = scrape_articles_from_profile(researcher_google_scholar_url)
            # add a progress bar to show the progress of scraping the details for the articles
            for article in tqdm(articles, desc="Scraping article details"):
                article_google_scholar_url = article['article_google_scholar_url']
                research_paper_publication_year = article['research_paper_publication_year']
                article_details = extract_article_details(article_google_scholar_url, research_paper_publication_year, author_id)

                if isinstance(article_details, str) and article_details.startswith("Error"):
                    print(f"Skipping article due to error: {article_details}")
                    continue
                # if open ai api key is there, then classify the paper
                if openai.api_key:
                    classification, language = classify_paper(article_details["research_paper_title"], article_details["abstract"],subthemes)
                    article_details["article_theme"] = classification
                    article_details["language"] = language
                    all_article_details.append(article_details)
                    # exclude the paper that is not related to sustainability
                    if not classification.lower().startswith("exclude"):
                        sus_article_details.append(article_details)
                        author_details = extract_author_details(article_details['research_paper_title'], article_google_scholar_url)
                        if author_details:
                            if author_details != "CAPTCHA":
                                sus_author_details.extend(author_details)
                            else:
                                all_article_details.to_excel(f"{user_name} paper_scrapper_CAPTCHA_detected.xlsx")
                                print("==============The code exit due to CAPTCHA detected, articles scrapped already saved to path==============")
                                sys.exit()
                else:
                    article_details["article_theme"] = "No API key"
                    article_details["language"] = "No API key"
                    all_article_details.append(article_details)
                    sus_article_details.append(article_details)
                    author_details = extract_author_details(article_details['research_paper_title'], article_google_scholar_url)
                    if author_details:
                        if author_details != "CAPTCHA":
                            sus_author_details.extend(author_details)
                        else:
                            pd.DataFrame(all_article_details).to_excel(f"{user_name} paper_scrapper_CAPTCHA_detected.xlsx")
                            print("==============The code exit due to CAPTCHA detected, articles scrapped already saved to path==============")
                            sys.exit()

        else:
            print("No profile found")

    sus_article_df = pd.DataFrame(sus_article_details)
    author_df = pd.DataFrame(sus_author_details)

    article_table, author_table = clean_and_merge_data(sus_article_df, author_df)

    profile_df = pd.DataFrame(all_google_scholar_urls)
    article_df = pd.DataFrame(all_article_details)

    datetime_proceed = timestamp()

    writer = pd.ExcelWriter(f"{user_name} paper_scrapper_results {datetime_proceed}.xlsx")
    pd.DataFrame(profile_df).to_excel(writer, sheet_name='google_scholar_url', index=False)
    pd.DataFrame(all_article_details).to_excel(writer, sheet_name='all_article', index=False)
    pd.DataFrame(article_table).to_excel(writer, sheet_name='sus_article_table', index=False)
    pd.DataFrame(author_table).to_excel(writer, sheet_name='sus_author_table', index=False)
    writer.close()
    print("Data extraction and cleaning completed and saved to Excel workbook with multiple sheets.")

if __name__ == "__main__":
    main()
