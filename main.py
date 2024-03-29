from typing import Dict, List, Literal, Optional
from urllib.parse import quote

import requests

import json

HIDDEN_URL = "https://www.justetf.com/servlet/etfs-table"
BASE_PARAMS = {
    "draw": 1,
    "start": 0,
    "length": -1,
    "lang": "en",
    "country": "IT",
    "universeType": "private",
}

InstrumentType = Optional[Literal["ETC", "ETF", "ETN"]]

INSTRUMENTS: Dict[InstrumentType, str] = {
    "ETC": "ETC",
    "ETF": "ETF",
    "ETN": "ETN",
}


def build_query(instrument: Optional[InstrumentType] = None) -> str:
    params = "groupField=index&productGroup=epg-longOnly"  # Default strategy
    if instrument is not None:
        params += f"&instrumentType={instrument}"
    return params


def make_request(instrument: Optional[InstrumentType] = None) -> List[Dict[str, str]]:
    query = build_query(instrument)
    print(instrument)
    print("Query: " + str(query))
    response = requests.post(
        HIDDEN_URL,
        {
            **BASE_PARAMS,
            "etfsParams": query,
        },
    )
    assert response.status_code == requests.codes.ok
    data = response.json()["data"]
    return data


def create_hashmap_by_key(etf_data: List[Dict[str, str]], key: str) -> Dict[str, Dict[str, str]]:
    isin_hashmap = {element[key]: element for element in etf_data}
    return isin_hashmap

def print_etf_info(hashmap: Dict[str, Dict[str, str]], key: str) -> Dict[str, str]:
    selected_etf = hashmap.get(key)
    print(
        f'''
        \nETF Information:
        
        - Name: {selected_etf["name"]}
        - ISIN: {selected_etf["isin"]}
        - Ticker: {selected_etf["ticker"]}
        - Distribution Policy: {selected_etf["distributionPolicy"]}
        - TER: {selected_etf["ter"]}
        - Found Currency: {selected_etf["fundCurrency"]}
        - Inception Date: {selected_etf["inceptionDate"]}
        - 1 Year Returns: {selected_etf["yearReturn1CUR"]}
        - Found Size: {selected_etf["fundSize"]} mln
        - Current Dividend Yield: {selected_etf["currentDividendYield"]}
        ''')
    return selected_etf
    
def find_similar_etfs(etf: Dict[str, str]):
    url_encoded_index = etf["groupValue"]
    response = requests.post(
        HIDDEN_URL,
        {
            **BASE_PARAMS,
            "etfsParams": f"groupField=index&index={url_encoded_index}",
        },
    )
    assert response.status_code == requests.codes.ok
    etf_list = response.json()["data"]
    sorted_etf_list = sorted(etf_list, key=lambda x: x.get('fundSize', 0))
    sorted_etf_list = [item for item in sorted_etf_list if item.get('ticker') != etf["ticker"]]
    if len(sorted_etf_list) > 5:
        sorted_etf_list = sorted_etf_list[:5]
    elif len(sorted_etf_list) == 0:
        print(f"There aren't other ETFs with the index: {etf['groupValue']}")
        return sorted_etf_list

    print("Here are other ETFs with the same index: \n")
    for selected_etf in sorted_etf_list:
        print(
        f'''
        \nETF Information:
        
        - Name: {selected_etf["name"]}
        - ISIN: {selected_etf["isin"]}
        - Ticker: {selected_etf["ticker"]}
        - Distribution Policy: {selected_etf["distributionPolicy"]}
        - TER: {selected_etf["ter"]}
        - Found Currency: {selected_etf["fundCurrency"]}
        - Inception Date: {selected_etf["inceptionDate"]}
        - 1 Year Returns: {selected_etf["yearReturn1CUR"]}
        - Found Size: {selected_etf["fundSize"]} mln
        - Current Dividend Yield: {selected_etf["currentDividendYield"]}
        ''')
    return etf_list
    


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
                etf = print_etf_info(isin_map, user_isin)
                find_similar_etfs(etf)
            else:
                print(f"\nETF with ISIN {user_isin} not found.")
        elif choice == "2":
            user_ticker = input("Enter a Ticker to retrieve information: ")
            selected_etf = ticker_map.get(user_ticker)
            if selected_etf:
                etf = print_etf_info(ticker_map, user_ticker)
                find_similar_etfs(etf)
            else:
                print(f"\nETF with ISIN {user_isin} not found.")
