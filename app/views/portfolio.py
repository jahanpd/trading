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
    portfolio, tickers, update = None, None, None
    if transactions is not None:
        # convert to list of objects/transactions
        trans_list = []
        for key in transactions:
            if transactions[key]['open']:
                trans_list.append(transactions[key])
        # sort list by opening date
        trans_list.sort(
            key=lambda x: datetime.datetime.fromisoformat(x['open_date']),
            reverse=False)
        tickers = list(set([d['ticker'] for d in trans_list]))
        # combine multiple transactions/tickers into one portfolio item
        portfolio = []
        for t in tickers:
            subset = [d for d in trans_list if d['ticker'] == t]
            if len(subset) == 1:
                portfolio.append(subset[0])
            else:
                open_price = np.array([d['open_price'] for d in subset])
                open_quant = np.array([d['open_quant'] for d in subset])
                open_value = np.array([d['open_value'] for d in subset])
                comb_value = np.sum(open_price * open_quant)
                dates = ', '.join([str(d['open_date']) for d in subset])
                position = {
                "ticker":t,
                "open":True,
                "assett":subset[0]["assett"],
                "name": subset[0]["name"],
                "sector":subset[0]["sector"],
                "market":subset[0]["market"],
                "currency":subset[0]["currency"],
                "open_date":dates,
                "open_price": comb_value / np.sum(open_quant),
                "open_quant": np.sum(open_quant),
                "open_value": comb_value,
                "close_date":"empty",
                "close_price": 0,
                "close_quant": 0,
                "close_value": 0
                }
                portfolio.append(position)
        portfolio.sort(
            key=lambda x: datetime.datetime.fromisoformat(x['open_date']),
            reverse=True)

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
            if len(tickers) > 1:
                cv = data_long['Close'][t].dropna().values[-1],
                update[t] = {
                    "close_price": cv,
                    "volume": data_long['Volume'][t].dropna().values[-1],
                    "close_value": cv[0] * subset[0]["open_quant"],
                    "market": subset[0]["market"],
                    "sector": subset[0]["sector"],
                    "assett": subset[0]["assett"],
                    "au_index": index_data['Close']["^AXJO"].dropna().values[-1],
                    "us_index": index_data['Close']["^GSPC"].dropna().values[-1]
                    }
            else:
                cv = data_long['Close'].dropna().values[-1],
                update[t] = {
                    "close_price": cv[0],
                    "volume": data_long['Volume'].dropna().values[-1],
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

        # print(portfolio)
        # print(tickers)
        print(m_dict_long)
    return render_template(
        'portfolio.html',
        transactions=transactions,
        portfolio=portfolio,
        tickers=tickers,
        update=update,
        totals=totals,
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
        start = dt - datetime.timedelta(days=5)
        end = dt + datetime.timedelta(days=5)
        data = yf.download(ticker, start=start, end=end)
        t = yf.Ticker(ticker)
        d = t.info
        if assett == '2':
            d['sector'] = "cryptocurrency"
        if assett == '3':
            d['sector'] = "ETF"
        idx = np.argmin(np.abs((data.index - dt).values.astype(float)))
        purch_price = data['Close'].values[idx]
        position = {
                "ticker":ticker,
                "open":True,
                "assett":assett,
                "name": d['shortName'],
                "sector":d['sector'],
                "market":d['market'],
                "currency":d["currency"],
                "open_date":str(dt),
                "open_price": purch_price,
                "open_quant": quant,
                "open_value": purch_price * quant,
                "close_date":"empty",
                "close_price": 0,
                "close_quant": 0,
                "close_value": 0
            }
        db.child("portfolio").child(userID).push(position, current_user.idToken)
        return redirect(url_for('portfolio.portfolio_view'))
    return render_template('open_position.html', form=form)