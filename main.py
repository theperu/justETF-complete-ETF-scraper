from typing import Dict, List, Literal, Optional

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
    response = requests.post(
        HIDDEN_URL,
        {
            **BASE_PARAMS,
            "etfsParams": build_query(instrument),
        },
    )
    assert response.status_code == requests.codes.ok
    data = response.json()["data"]
    return data


if __name__ == "__main__":
    result = make_request()

    etf_count = len(result)
    print(f"Found {etf_count} ETFs.")

    with open("etf_data.json", "w") as json_file:
        json.dump(result, json_file, indent=2)

    print("ETF data has been written to etf_data.json")
