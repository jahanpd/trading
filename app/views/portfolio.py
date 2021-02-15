import yfinance as yf
import datetime
import pandas as pd
import numpy as np
from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import login_required, current_user
from app import db
from app.forms.open_position import OpenPosition
from app.indicators.statistics import metrics

portfolio = Blueprint('portfolio', __name__,
                 template_folder='templates',
                 static_folder='static')


@portfolio.route('/portfolio', methods=['GET', 'POST'])
@login_required
def portfolio_view():
    userID = current_user.localId
    # retrieve portfolio object
    transactions = db.child("portfolio").child(userID).get(current_user.idToken)
    transactions = transactions.val()
    portfolio, tickers, update, totals = None, None, None, None
    m_dict_long, m_dict_short = None, None
    if transactions is not None:
        # convert to list of objects/transactions
        trans_list = []
        for key in transactions:
            trans_list.append(transactions[key])
        # sort list by opening date
        trans_list.sort(
            key=lambda x: datetime.datetime.fromisoformat(x['date']),
            reverse=False)
        tickers = list(set([d['ticker'] for d in trans_list]))
        # combine multiple transactions/tickers into one portfolio item
        portfolio = []
        closed = []
        for t in tickers:
            subset = [d for d in trans_list if d['ticker'] == t]
            if len(subset) == 1:
                portfolio.append(subset[0])
            else:
                avg_price = 0
                cum_quant = 0
                open_us_idx = 0
                open_au_idx = 0
                total_take = 0
                date = "replace"
                for doc in subset:
                    if doc['open']:
                        value = doc['open_quant'] * doc['open_price']
                        cum_value = (avg_price * cum_quant) + value
                        us_index_value = doc['open_quant'] * doc['us_index']
                        au_index_value = doc['open_quant'] * doc['au_index']
                        cum_us_index_value = (open_us_idx * cum_quant) + us_index_value
                        cum_au_index_value = (open_au_idx * cum_quant) + au_index_value
                        
                        cum_quant += doc['open_quant']
                        avg_price = value / cum_quant
                        open_us_idx = cum_us_index_value / cum_quant
                        open_au_idx = cum_au_index_value / cum_quant

                        date = str(doc['date'])
                        
                    else:
                        take = (doc['close_quant'] * doc['close_price'])\
                            - (avg_price * doc['close_quant'])
                        cum_quant -= doc['close_quant']
                        closed_pozzy = {
                            "ticker":t,
                            "assett":subset[0]["assett"],
                            "name": subset[0]["name"],
                            "sector":subset[0]["sector"],
                            "market":subset[0]["market"],
                            "currency":subset[0]["currency"],
                            "date":str(doc['date']),
                            "open_price": avg_price,
                            "open_quant": cum_quant,
                            "open_value": avg_price*doc['close_quant'],
                            "close_price": doc['close_price'],
                            "close_quant": doc['close_quant'],
                            "close_value": doc['close_quant'] * doc['close_price'],
                            "au_index": open_au_idx,
                            "us_index": open_us_idx,
                            "take":take
                            }
                        closed.append(closed_pozzy)

                if cum_quant > 0:
                    position = {
                    "ticker":t,
                    "open":True,
                    "assett":subset[0]["assett"],
                    "name": subset[0]["name"],
                    "sector":subset[0]["sector"],
                    "market":subset[0]["market"],
                    "currency":subset[0]["currency"],
                    "date":date,
                    "open_price": avg_price,
                    "open_quant": cum_quant,
                    "open_value": avg_price*cum_quant,
                    "close_price": 0,
                    "close_quant": 0,
                    "close_value": 0,
                    "au_index": open_au_idx,
                    "us_index": open_us_idx
                    }
                    portfolio.append(position)

        # find most recent price for each item
        tickers_string = ' '.join(tickers)
        start_long = datetime.datetime.now() - datetime.timedelta(days=180)
        start_short = datetime.datetime.now() - datetime.timedelta(days=14)
        data_long = yf.download(tickers_string, start=start_long)
        data_short = yf.download(tickers_string, start=start_short, interval='15m')

        indexes = "^AXJO ^GSPC"
        index_data=  yf.download(indexes, start=start_long)
        m_dict_long, _ = metrics(data_long['Close'])
        m_dict_short, _ = metrics(data_short['Close'])
        update = {}
        tickers = [d['ticker'] for d in portfolio]
        for t in tickers:
            subset = [d for d in portfolio if d['ticker'] == t]
            data_source = data_short
            if len(tickers) > 1:
                cv = data_source['Close'][t].dropna().values[-1],
                update[t] = {
                    "close_price": cv[0],
                    "open_quant": subset[0]["open_quant"],
                    "volume": data_source['Volume'][t].dropna().values[-1],
                    "close_value": cv[0] * subset[0]["open_quant"],
                    "market": subset[0]["market"],
                    "sector": subset[0]["sector"],
                    "assett": subset[0]["assett"],
                    "au_index": index_data['Close']["^AXJO"].dropna().values[-1],
                    "us_index": index_data['Close']["^GSPC"].dropna().values[-1]
                    }
            else:
                cv = data_source['Close'].dropna().values[-1],
                update[t] = {
                    "close_price": cv[0],
                    "volume": data_source['Volume'].dropna().values[-1],
                    "close_value": cv * subset[0]["open_quant"],
                    "market": subset[0]["market"],
                    "sector": subset[0]["sector"],
                    "assett": subset[0]["assett"],
                    "au_index": index_data['Close']["^AXJO"].dropna().values[-1],
                    "us_index": index_data['Close']["^GSPC"].dropna().values[-1]
                    }
        
        # work out sector totals by market and assett
        # aus equity
        totals = {}
        totals["aus_equity_open"] = np.sum([d["open_value"] for d in portfolio
            if (d["assett"] == "1") and (d["market"] == "au_market")]) 

        totals["aus_equity_close"] = np.sum([update[key]["close_value"] for key in update
            if (update[key]["assett"] == "1") and (update[key]["market"] == "au_market")])

        totals["us_equity_open"] = np.sum([d["open_value"] for d in portfolio
            if (d["assett"] == "1") and (d["market"] == "us_market")]) 

        totals["us_equity_close"] = np.sum([update[key]["close_value"] for key in update
            if (update[key]["assett"] == "1") and (update[key]["market"] == "us_market")])

        totals["aus_etf_open"] = np.sum([d["open_value"] for d in portfolio
            if (d["assett"] == "3") and (d["market"] == "au_market")]) 

        totals["aus_etf_close"] = np.sum([update[key]["close_value"] for key in update
            if (update[key]["assett"] == "3") and (update[key]["market"] == "au_market")])

        totals["us_etf_open"] = np.sum([d["open_value"] for d in portfolio
            if (d["assett"] == "3") and (d["market"] == "us_market")]) 

        totals["us_etf_close"] = np.sum([update[key]["close_value"] for key in update
            if (update[key]["assett"] == "3") and (update[key]["market"] == "us_market")])

        totals["crypto_open"] = np.sum([d["open_value"] for d in portfolio
            if (d["assett"] == "2")]) 

        totals["crypto_close"] = np.sum([update[key]["close_value"] for key in update
            if (update[key]["assett"] == "2") ])

        # get transaction deletion input
        if request.method == 'POST':
            for key in request.form:
                if request.form[key] == "delete":
                    db.child("portfolio").child(userID).child(key)\
                        .remove(current_user.idToken)
            return redirect(url_for('portfolio.portfolio_view'))

    portfolio.sort(key=lambda d: update[d["ticker"]]["close_value"] / d["open_value"], reverse=True)
    tickers = [d['ticker'] for d in portfolio]
    # print(transactions)
    # print(tickers)
    return render_template(
        'portfolio.html',
        transactions=transactions,
        portfolio=portfolio,
        tickers=tickers,
        update=update,
        totals=totals,
        closed=closed,
        metrics_long=m_dict_long,
        metrics_short=m_dict_short
        )

@portfolio.route('/open_position', methods=['GET', 'POST'])
@login_required
def open_position():
    form = OpenPosition()
    if form.validate_on_submit():
        now = str(datetime.datetime.now())
        userID = current_user.localId
        ticker = form.ticker.data
        dt = form.datetime_added.data
        quant = form.quantity.data
        assett = form.assett.data
        cost = form.cost.data
        start = dt - datetime.timedelta(days=5)
        end = dt + datetime.timedelta(days=5)
        data = yf.download(ticker, start=start, end=end)
        indexes = "^AXJO ^GSPC"
        index_data = yf.download(indexes, start=start, end=end)
        t = yf.Ticker(ticker)
        d = t.info
        if assett == '2':
            d['sector'] = "cryptocurrency"
        if assett == '3':
            d['sector'] = "ETF"
        idx = np.argmin(np.abs((data.index - dt).values.astype(float)))
        idx_index = np.argmin(np.abs((index_data['Close'].dropna().index - dt).values.astype(float)))
        index_value = index_data['Close'].dropna().values[idx_index, :]
        if form.price.data is None:
            purch_price = data['Close'].values[idx]
        else:
            purch_price = form.price.data
        position = {
                "ticker":ticker,
                "open":True,
                "assett":assett,
                "name": d['shortName'],
                "sector":d['sector'],
                "market":d['market'],
                "currency":d["currency"],
                "date":str(dt),
                "open_price": purch_price,
                "open_quant": quant,
                "open_value": purch_price * quant,
                "open_cost": cost,
                "close_price": 0,
                "close_quant": 0,
                "close_value": 0,
                "close_cost": 0,
                "au_index": index_value[0],
                "us_index": index_value[1]
            }
        print(position)
        db.child("portfolio").child(userID).push(position, current_user.idToken)
        return redirect(url_for('portfolio.portfolio_view'))
    return render_template('open_position.html', form=form)

@portfolio.route('/close_position', methods=['GET', 'POST'])
@login_required
def close_position():
    form = OpenPosition()
    print("close_position")
    if form.validate_on_submit():
        print("validated")
        now = str(datetime.datetime.now())
        userID = current_user.localId
        ticker = form.ticker.data
        dt = form.datetime_added.data
        quant = form.quantity.data
        assett = form.assett.data
        cost = form.cost.data
        start = dt - datetime.timedelta(days=5)
        end = dt + datetime.timedelta(days=5)
        data = yf.download(ticker, start=start, end=end)
        indexes = "^AXJO ^GSPC"
        index_data = yf.download(indexes, start=start, end=end)
        t = yf.Ticker(ticker)
        d = t.info
        if assett == '2':
            d['sector'] = "cryptocurrency"
        if assett == '3':
            d['sector'] = "ETF"
        idx = np.argmin(np.abs((data.index - dt).values.astype(float)))
        idx = np.argmin(np.abs((data.index - dt).values.astype(float)))
        idx_index = np.argmin(np.abs((index_data['Close'].dropna().index - dt).values.astype(float)))
        index_value = index_data['Close'].dropna().values[idx_index, :]
        if form.price.data is None:
            purch_price = data['Close'].values[idx]
        else:
            purch_price = form.price.data
        position = {
                "ticker":ticker,
                "open":False,
                "assett":assett,
                "name": d['shortName'],
                "sector":d['sector'],
                "market":d['market'],
                "currency":d["currency"],
                "open_price": 0,
                "open_quant": 0,
                "open_value": 0,
                "open_cost": 0,
                "date":str(dt),
                "close_price": purch_price,
                "close_quant": quant,
                "close_value": purch_price * quant,
                "close_cost": cost,
                "au_index": index_value[0],
                "us_index": index_value[1]
            }
        print(position)
        db.child("portfolio").child(userID).push(position, current_user.idToken)
        return redirect(url_for('portfolio.portfolio_view'))
    return render_template('open_position.html', form=form)