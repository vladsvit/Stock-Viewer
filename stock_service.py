from models import db, Stock, StockPrice
from decimal import Decimal
import datetime
from api import fetch_stock_json



def find_stock(stock_symbol):
    stock = db.session.execute(db.select(Stock).where(Stock.symbol == stock_symbol)).scalar_one_or_none()
    return stock

def find_stock_data(stock_symbol):
    stock = find_stock(stock_symbol)
    today = str(datetime.date.today())
    needs_fetch = (stock is None or stock.last_fetched_at != str(today))
    if needs_fetch:
        data_json = fetch_stock_json(stock_symbol)

        if "error" in data_json or not data_json.get("data"):
            return "error"

        if stock is None:
            stock = Stock(symbol=stock_symbol, company_name=data_json["data"][0]["name"])
            db.session.add(stock)
            db.session.flush()

        save_stock_prices(stock, data_json)
        stock.last_fetched_at = today
        db.session.commit()

    else:
        data_json = get_cached_stock_data(stock)
    return data_json

def delete_stock(stock_id):
    stock = db.get_or_404(Stock, stock_id)
    print(f"Stock {stock.symbol} deleted")
    db.session.delete(stock)
    db.session.commit()

def save_stock_prices(stock, data_json):
    for record in data_json["data"]:
        day = record["date"][:10]

        existing_price = db.session.execute(
            db.select(StockPrice).where(
                StockPrice.stock_id == stock.id,
                StockPrice.date == day
            )
        ).scalar_one_or_none()

        if existing_price is None:
            new_price = StockPrice(
                stock_id=stock.id,
                date=day,
                close=Decimal(str(record["close"])),
                open=Decimal(str(record["open"])),
                high=Decimal(str(record["high"])),
                low=Decimal(str(record["low"])),
                volume=int(record["volume"]),
                adj_close=Decimal(str(record["adj_close"])),
            )
            db.session.add(new_price)

def get_cached_stock_data(stock):
    today = datetime.date.today()

    if str(today) != stock.last_fetched_at:
        last_fetched_at = datetime.datetime.fromisoformat(stock.last_fetched_at)
        start_date = last_fetched_at - datetime.timedelta(days=30)
        print("Cached data is old. Showing the latest cached data.")
        stock_prices = db.session.execute(
            db.select(StockPrice)
            .where(
                StockPrice.stock_id == stock.id,
                StockPrice.date.between(start_date, last_fetched_at)
            )
            .order_by(StockPrice.date.desc())
        ).scalars().all()
    else:
        start_date = today - datetime.timedelta(days=30)
        print("Latest data available")
        stock_prices = db.session.execute(
            db.select(StockPrice)
            .where(
                StockPrice.stock_id == stock.id,
                StockPrice.date.between(start_date, today)
            )
            .order_by(StockPrice.date.desc())
        ).scalars().all()

    data_json = {"data": [
            {
                "close": float(price.close),
                "date": price.date
            }
            for price in stock_prices
        ]
    }

    return data_json


def get_watchlist_data():
    stocks = db.session.execute(db.select(Stock).order_by(Stock.symbol)).scalars().all()
    returns = {item.symbol: round(100*(item.prices[-1].close - item.prices[0].close)/item.prices[0].close, 2) for item in stocks}
    return stocks, returns