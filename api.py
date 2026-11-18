import requests
import os
import datetime as dt
import pandas as pd

my_email = os.environ.get("ENV_EMAIL")
API_KEY = os.environ.get("ENV_API_KEY")

# out_email = os.environ.get("ENV_OUT_EMAIL")
# password = os.environ.get("ENV_EMAIL_APP_PASSWORD")
# message_to_send = ""

url_endpoint = "https://api.marketstack.com/v2/eod"

def fetch_stock_json(stock_symbol):
    stock_symbol = stock_symbol.strip().upper()
    if stock_symbol == "TEST":
        return {}

    today = dt.date.today()
    thirty_day_ago = today - dt.timedelta(days=30)
    stock_parameters = {
        "access_key": API_KEY,
        "symbols": stock_symbol,
        "date_from": str(thirty_day_ago),
        "date_to": str(today)
    }

    try:
        response = requests.get(
            url=url_endpoint,
            params=stock_parameters,
            timeout=5,
        )
        return response.json()
    except requests.exceptions.Timeout:
        return {"error": {"message": "The stock service timed out."}}
    except requests.exceptions.ConnectionError:
        return {"error": {"message": "Could not connect to the stock service."}}

def analyze_json(fetched_json):
    if not fetched_json["data"]:
        return {"error":"No data available. Check the stock symbol used and for the correct parameters."}

    elif len(fetched_json["data"]) == 1:
        return {"error": "The data is not large enough to analyze"}

    last_close = fetched_json["data"][0]["close"]
    second_last_close = fetched_json["data"][1]["close"]
    thirty_day_ago_close = fetched_json["data"][-1]["close"]

    single_day_change = round(((last_close - second_last_close) / second_last_close) * 100, 2)
    thirty_day_change = round(((last_close - thirty_day_ago_close) / thirty_day_ago_close) * 100, 2)
    closes_list = [item["close"] for item in fetched_json["data"]][::-1]

    closes_series = pd.Series(closes_list)
    pct_change_series = closes_series.pct_change()
    day_close_changes = [round(item*100,2) for item in pct_change_series.to_list() if type(item) is float]
    print(day_close_changes)
    volatility = round(pd.Series(day_close_changes).std(),2)
    print(volatility)
    sma_5day_series = closes_series.rolling(window=5).mean()
    sma_20day_series = closes_series.rolling(window=20).mean()
    sma_5day = sma_5day_series.to_list()
    sma_20day = sma_20day_series.to_list()
    sma_5day = [round(item,2) for item in sma_5day if type(item) is float]
    sma_20day = [round(item,2) for item in sma_20day if type(item) is float]
    # print(sma_5day)
    # print(sma_20day)

    if len(fetched_json["data"][0]["date"]) < 11:
        # print("it's a string")
        dates_list = [item["date"] for item in fetched_json["data"]][::-1]

    else:
        # print("it's not a string")
        dates = [dt.datetime.strptime(item["date"], "%Y-%m-%dT%H:%M:%S%z") for item in fetched_json["data"]][::-1]
        dates_list = [item.strftime("%Y/%m/%d")for item in dates]


    return {
        "last_close": last_close,
        "single_day_change": single_day_change,
        "thirty_day_change": thirty_day_change,
        "first_close": thirty_day_ago_close,
        "closes_list": closes_list,
        "dates_list": dates_list,
        "rolling_5day": sma_5day,
        "rolling_20day": sma_20day,
        "highest": max(closes_list),
        "lowest": min(closes_list),
        "volatility": volatility
    }