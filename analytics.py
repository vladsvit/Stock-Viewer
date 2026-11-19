import datetime as dt
import pandas as pd
import datetime

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

"""calculates cumulative returns of 2 stocks over a 30 day period and returns a dictionary"""
def compare_returns(prices_dict):
    a_dates = {key for key in prices_dict["stock_a"]}
    b_dates = {key for key in prices_dict["stock_b"]}
    common_dates = sorted(a_dates & b_dates)
    if not common_dates:
        return {"error": "No common dates found."}

    a_price_lookup = prices_dict["stock_a"]
    b_price_lookup = prices_dict["stock_b"]
    cutoff_date = datetime.datetime.fromisoformat(common_dates[-1]) - datetime.timedelta(days=30)
    cutoff_date = cutoff_date.date().isoformat()

    common_dates = [item for item in common_dates if item >= cutoff_date]
    start_date = common_dates[0]
    stock_a_returns = [round(((a_price_lookup[item]-a_price_lookup[start_date])/a_price_lookup[start_date])*100, 2)
                       for item in common_dates]
    stock_b_returns = [round(((b_price_lookup[item]-b_price_lookup[start_date])/b_price_lookup[start_date])*100, 2)
                       for item in common_dates]

    return {
        "dates": common_dates,
        "stock_a_returns": stock_a_returns,
        "stock_b_returns": stock_b_returns,
    }
