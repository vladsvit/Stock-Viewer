import requests
import os
import datetime as dt

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

