import os
from api import fetch_stock_json
from analytics import analyze_json, compare_returns
import datetime
from flask import Flask, render_template, redirect, url_for, abort, flash, request, session
from typing import List
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Numeric
from flask_wtf.csrf import CSRFProtect
from decimal import Decimal
from models import db, Stock, StockPrice


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

    data_json = {
        "data": [
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


app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("FLASK_SECRET_KEY")
Bootstrap5(app)
CSRFProtect(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///stock_data.db'
db.init_app(app)

with app.app_context():
    db.create_all()

@app.context_processor
def inject_watchlist():
    stocks, returns = get_watchlist_data()
    return {
        "stocks": stocks,
        "returns": returns
    }

@app.route('/', methods=["POST", "GET"])
def main_graph():
    today = str(datetime.date.today())

    if request.method == "POST":
        stock_symbol = request.form["stock"].strip().upper()
        stock = db.session.execute(
            db.select(Stock).where(
                Stock.symbol == stock_symbol
            )
        ).scalar_one_or_none()

        # A missing stock or an outdated cache requires fetching.
        needs_fetch = (
                stock is None
                or stock.last_fetched_at != str(today)
        )

        if needs_fetch:
            data_json = fetch_stock_json(stock_symbol)

            # Don't save an invalid response.
            if "error" in data_json or not data_json.get("data"):
                flash("Unable to retrieve stock prices.")
                return redirect(url_for("main_graph"))

            if stock is None:
                stock = Stock(symbol=stock_symbol,company_name=data_json["data"][0]["name"])
                db.session.add(stock)

                # Assigns the database-generated stock.id.
                db.session.flush()

            save_stock_prices(stock, data_json)

            stock.last_fetched_at = today
            db.session.commit()

        else:
            data_json = get_cached_stock_data(stock)

        stock_dict = analyze_json(data_json)
        if "error" in stock_dict:
            print(stock_dict["error"])
            flash(f'There is an error. {stock_dict["error"]}')
            return redirect(url_for("main_graph"))

        stock_dict["company_name"] = stock.company_name
        return render_template("index.html", stock_dict=stock_dict, returns_dict=None, view="stock")
    return render_template("index.html", stock_dict=None, returns_dict=None)

@app.route("/stock/<symbol>", methods=["POST", "GET"])
def stock_detail(symbol):
    session["last_stock"] = symbol
    stock = db.session.execute(db.select(Stock).where(Stock.symbol == symbol)).scalar_one_or_none()

    if stock is None:
        abort(404, description="Stock not found in the watchlist.")

    data_json = get_cached_stock_data(stock)
    stock_dict = analyze_json(data_json)
    stock_dict["company_name"] = stock.company_name


    return render_template("index.html", stock_dict=stock_dict, view="stock")

@app.route("/stock")
def last_stock():
    symbol = session.get("last_stock")

    if symbol:
        return redirect(url_for("stock_detail", symbol=symbol))

    return redirect(url_for("main_graph", view="stock"))

@app.route("/compare", methods=["POST", "GET"])
def return_graph():
    if request.method == "POST":
        selected_stocks = request.form.getlist("stocks")
        if len(selected_stocks) != 2:
            flash(f'You have selected less or more than 2 stocks to compare')
            return redirect(url_for("main_graph"))

        session["selected_stocks"] = selected_stocks
        return redirect(url_for("return_graph"))

    else:
        selected_stocks = session.get("selected_stocks", [])

    if len(selected_stocks) != 2:
        return render_template("index.html", stock_dict=None, returns_dict=None ,view="compare")

    returns_dict = compare_returns(selected_stocks[0], selected_stocks[1])
    if "error" in returns_dict:
        session.pop("selected_stocks", None)
        flash(returns_dict["error"])
        return redirect(url_for("main_graph"))

    return render_template("index.html",stock_dict=None, returns_dict=returns_dict, view="compare")

@app.route('/delete/<stock_id>', methods=["POST"])
def remove_stock(stock_id):
    stock = db.get_or_404(Stock, stock_id)
    print(f"Stock {stock.symbol} deleted")

    # Deleting the stock is disabled temporarily to reduce necesary API calls, funcionality works right now
    db.session.delete(stock)
    db.session.commit()
    return redirect(url_for("main_graph"))


if __name__ == '__main__':
    app.run(debug=True, port=5004)
