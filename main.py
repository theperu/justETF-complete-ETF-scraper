import re
from typing import Dict, List, Literal, Optional
from bs4 import BeautifulSoup
from urllib.parse import quote
import urllib.parse
import warnings

import requests
import json

BASE_URL = "https://www.justetf.com/en/search.html"
BASE_DATA = {"draw": 1, "start": 0, "length": -1}
PATTERN = re.compile(
    r"(\d)-1.0-container-tabsContentContainer-tabsContentRepeater-1-container-content-etfsTablePanel&search=ETFS&_wicket=1"
)

def make_request(index: Optional[str] = None) -> List[Dict[str, str]]:
    with requests.Session() as session:
        html_response = session.get(f"{BASE_URL}?search=ETFS&index=Algorand")
        if not index:
            build_indexes_list(html_response)

        if match := PATTERN.search(html_response.text):
            counter = int(match.group(1))
        else:
            warnings.warn("Cannot parse dynamic counter from HTML page, assuming 0.")
            counter = 0

        url = f"{BASE_URL}?{counter}-1.0-container-tabsContentContainer-tabsContentRepeater-1-container-content-etfsTablePanel&search=ETFS&_wicket=1"
        payload = {
            **BASE_DATA,
            "lang": 'en',
            "country": 'DE',
            "universeType": 'private',
            "defaultCurrency": 'EUR',
        }

        if index:
            payload["etfsParams"] = f'search=ETFS&index={index}&query='
        response = session.post(url, payload)

    assert response.status_code == requests.codes.ok, f"Request failed with status {response.status_code}"
    return response.json().get("data", [])


def create_hashmap_by_key(etf_data: List[Dict[str, str]], key: str) -> Dict[str, Dict[str, str]]:
    isin_hashmap = {element[key]: element for element in etf_data}
    return isin_hashmap

def build_indexes_list(html_response: requests.Response):
    soup = BeautifulSoup(html_response.text, "html.parser")
    options = soup.find_all("option")

    options_dict = {int(option["value"]): option.text.strip() for option in options if option.has_attr("value") and option["value"].isdigit()}

    with open("indexes.json", "w") as file:
        json.dump(options_dict, file, indent=4)

def get_etf_index(etf: Dict[str, str] | None) -> str | None:
    if etf:
        with requests.Session() as session:
            html_response = session.get(f"https://www.justetf.com/en/etf-profile.html?isin={etf["isin"]}")

            with open("response.txt", "w", encoding="utf-8") as f:
                f.write(html_response.text)

            soup_table = BeautifulSoup(html_response.text, "html.parser")

            index_td = soup_table.find("td", string=" Index ")
            print(f"Found element: {index_td.text}")
            if index_td:
                index_name_td = index_td.find_next_sibling("td")
                if index_name_td:
                    index_name = index_name_td.get_text(strip=True)
                    print(f"\nYour ETF tracks the index: {index_name}")
                    return index_name
    return None


def print_etf_info(etf: Dict[str, str] | None):
    if etf:
        print(
            f'''
            \nETF Information:
            
            - Name: {etf["name"]}
            - ISIN: {etf["isin"]}
            - Ticker: {etf["ticker"]}
            - Distribution Policy: {etf["distributionPolicy"]}
            - TER: {etf["ter"]}
            - Found Currency: {etf["fundCurrency"]}
            - Inception Date: {etf["inceptionDate"]}
            - 1 Year Returns: {etf["yearReturn1CUR"]}
            - Found Size: {etf["fundSize"]} mln
            - Current Dividend Yield: {etf["currentDividendYield"]}
            ''')

    
def find_similar_etfs(index: str | None, etf: str):
    if index:
        # Convert index string for search
        encoded_index = urllib.parse.quote(index, safe='')

        # Get ETF with same index
        data = make_request(index=encoded_index)
        
        # Filter the first 5 by size and return results
        filtered_data = [item for item in data if item.get("isin") != etf["isin"]]
        if filtered_data:
            print(f"\n\nHere are some similar etfs to the index: {index}\n")
            for etf in filtered_data[:5]:
                print_etf_info(etf)
        return
    print(f"There aren't other ETFs with the index: {index}")
    


if __name__ == "__main__":
    result = make_request()

    etf_count = len(result)
    print(f"Found {etf_count} ETFs.")

    with open("etf_data.json", "w") as json_file:
        json.dump(result, json_file, indent=2)

    print("ETF data has been written to etf_data.json\n")

    isin_map = create_hashmap_by_key(result, "isin")
    ticker_map = create_hashmap_by_key(result, "ticker")
    print("Welcome to JustETF Complete ETF Scraper!\n")

    choice = 0
    while choice != "3":
        print("What do you want to do?\n - Press 1 to lookup an ETF by ISIN\n - Press 2 to lookup an ETF by ticker\n - Press 3 to exit the script\n")
        choice = input("Enter your choice: ")
        if choice == "1":
            user_isin = input("Enter an ISIN to retrieve information: ")
            selected_etf = isin_map.get(user_isin)
            if selected_etf:
                print_etf_info(selected_etf)
                index = get_etf_index(selected_etf)
                find_similar_etfs(index, selected_etf)
            else:
                print(f"\nETF with ISIN {user_isin} not found.")
        elif choice == "2":
            user_ticker = input("Enter a Ticker to retrieve information: ")
            selected_etf = ticker_map.get(user_ticker)
            if selected_etf:
                print_etf_info(selected_etf)
                index = get_etf_index(selected_etf)
                find_similar_etfs(index, selected_etf)
            else:
                print(f"\nETF with ISIN {user_isin} not found.")
