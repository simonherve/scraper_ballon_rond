import streamlit as st

import time
import pandas as pd
import time
import pickle
import numpy as np
from selenium import webdriver
path = "C:\Program Files (x86)\chromedriver.exe"
from selenium.webdriver.common.by import By
import os
import sys
import pandas as pd
from nordvpn_switcher import initialize_VPN, rotate_VPN
from bs4 import BeautifulSoup



def crawling_match_url(path, region_number, tournaments_number, season_number, api_delay_term=5):
    rotate_VPN()
    bar = st.progress(0)
    # activate webdriver
    url = 'https://www.whoscored.com/Regions/'+str(region_number)+'/Tournaments/'
    url = url+str(tournaments_number)+'/Seasons/'+str(season_number)+'/Fixtures'
    driver = webdriver.Chrome(path)
    driver.get(url)

    # wait get league team datas
    match_link= []
    #with tqdm(total=40, file=sys.stdout) as pbar :
    for i in range(1):
        time.sleep(api_delay_term)
        elements = driver.find_elements_by_css_selector('a.result-1.rc')
        for element in elements:
            match_link.append(element.get_attribute('href'))

            # click
        try : 
            button = driver.find_element_by_css_selector('a.previous.button.ui-state-default.rc-l.is-default')
            driver.execute_script("arguments[0].click();", button)
            bar.progress(i*2)
            
        except : 
            bar.progress(80)
            break

        time.sleep(2)
            
    
    driver.close()
    ids = []
    for url in list(set(match_link)):
        ids.append(url.split("Matches/")[1].split("/Live")[0])
    bar.progress(100)
    return ids

def get_data(soup):

    script = soup.find_all("script")
    for i in range(30,45): 
        
        try:
            data = str(script[i])
            data = data.split('<script>\n        require.config.params["args"] = ')[1]
            data = data.split(';\n    </script>')[0]
            data = data.replace("matchId", '"matchId"')
            data = data.replace("matchCentreData", '"matchCentreData"')
            data = data.replace("matchCentreEventTypeJson", '"matchCentreEventTypeJson:"')
            data = data.replace("formationIdNameMappings", '"formationIdNameMappings"')
            return data
        except:
            pass
    return -1

def page_verification(soup):

    script = soup.find_all("script")
    for i in range(20,45): 
        
        try:
            data = str(script[i])
            data = data.split('input: [')[1]
            data = data.split(']')[0]
            data = data.split(",") 
            return [elem.replace("'", "") for elem in data]
        except:
            pass
    return -1

def parse_file(html):
    soup = BeautifulSoup(html, "html.parser")
    verification = page_verification(soup)
    if (verification[7] == "FIN"):
        return get_data(soup)
    else:
        return None

def scraper_json(savedFile, links):
    links = [int(link) for link in links]
    bar = st.progress(0)
    error_count = 0
    dico = {"id":[], "data":[]} # Initialisation du dictionnaire
    index = 0 
    len_ = len(links)
    for link in links: 
        if index%10 == 0:
            rotate_VPN()  
        index +=1
        bar.progress(index/len_) 
        cond_ = 0
        while cond_ < 4:
            try:
                driver = webdriver.Chrome(path)
                driver.get(f"https://fr.whoscored.com/Matches/{link}/live/")
                html = driver.page_source
                data = parse_file(html)
                if data is None:
                    print("> No data!")
                    cond_ = 4
                else:
                    dico["id"].append(link)
                    dico["data"].append(data)
                    cond_ = 4
            except Exception as e:
                error_count +=1
                print(f"> [Error] {e}")
                rotate_VPN()
                cond_ += 1
        
    driver.close()
    dico = pd.DataFrame(dico)
    dico.to_csv(savedFile+".csv")
    st.write(f"Number errors = {error_count}")
    
initialize_VPN(save=1,area_input=["Norway", "Australia", "Canada", "Taiwan", "Brazil", "United States", "Mexico"])

st.sidebar.header("Input parameter")
with st.sidebar.form(key="my_form"):#, clear_on_submit=False):
    region = st.text_input("Enter region number:")
    tournament = st.text_input("Enter tournament number:")
    season = st.text_input("Enter season number:")
    file_name = st.text_input("Enter the name of the file")
    submit_button = st.form_submit_button(label="submit")

st.markdown("# Scraper WhoScored?com")
if submit_button:
    st.markdown("## Step 1: Retrieve matchs URLs")
    ids = crawling_match_url(path, region, tournament, season)
    st.markdown("## Step 2: Retrieve matchs Json")
    scraper_json(file_name, ids)

