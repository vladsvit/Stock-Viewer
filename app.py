import os
from analytics import analyze_json, compare_returns
from flask import Flask, render_template, redirect, url_for, abort, flash, request, session
from flask_bootstrap import Bootstrap5
from flask_wtf.csrf import CSRFProtect
from models import db
from stock_service import get_cached_stock_data, get_watchlist_data, find_stock_data, delete_stock, \
    find_stock, get_prices_for_stock

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
    if request.method == "POST":
        stock_symbol = request.form["stock"].strip().upper()
        data = find_stock_data(stock_symbol)
        if "error" in data:
            flash(data["error"])
            return redirect(url_for("main_graph"))

        stock_dict = analyze_json(data["data_json"])
        if "error" in stock_dict:
            print(stock_dict["error"])
            flash(f'There is an error. {stock_dict["error"]}')
            return redirect(url_for("main_graph"))

        stock_dict["company_name"] = data["company_name"]
        return render_template("index.html", stock_dict=stock_dict, returns_dict=None, view="stock")
    return render_template("index.html", stock_dict=None, returns_dict=None)

@app.route("/stock/<symbol>", methods=["POST", "GET"])
def stock_detail(symbol):
    session["last_stock"] = symbol
    stock = find_stock(symbol)
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

    stock_prices_dicts = get_prices_for_stock(selected_stocks[0], selected_stocks[1])
    if "error" in stock_prices_dicts:
        session.pop("selected_stocks", None)
        flash(stock_prices_dicts["error"])
        return redirect(url_for("main_graph"))

    returns_dict = compare_returns(stock_prices_dicts)
    if "error" in returns_dict:
        session.pop("selected_stocks", None)
        flash(returns_dict["error"])
        return redirect(url_for("main_graph"))

    returns_dict["stock_a"] = selected_stocks[0]
    returns_dict["stock_b"] = selected_stocks[1]
    return render_template("index.html",stock_dict=None, returns_dict=returns_dict, view="compare")

@app.route('/delete/<stock_id>', methods=["POST"])
def remove_stock(stock_id):
    delete_stock(stock_id)
    return redirect(url_for("main_graph"))

if __name__ == '__main__':
    app.run(debug=True, port=5004)
