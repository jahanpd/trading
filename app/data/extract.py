import numpy as np
import pandas as pd
import yfinance as yf
import datetime
import pytz
from statsmodels.tsa.stattools import adfuller
from hurst import compute_Hc, random_walk
from scipy.stats import skew, kurtosis
from indicators.MaasoumiZaman import MZ

tickers = pd.read_csv('stake_tickers.csv')
tickers = list(tickers.Ticker.values)
# tickers = ["AAPL", "TSLA", "MSFT"]

tickers_string = ' '.join(tickers)
start_long = datetime.datetime.now() - datetime.timedelta(days=180)
start_short = datetime.datetime.now() - datetime.timedelta(days=14)

midpoint = datetime.datetime.now() - datetime.timedelta(days=7)

data_long = yf.download(tickers_string, start=start_long)
long_close = data_long["Close"]
long_volume = data_long["Volume"]
long_close.dropna(axis=0, how="all", inplace=True)
long_close.dropna(axis=1, how="any", inplace=True)
long_volume.dropna(axis=0, how="all", inplace=True)
long_volume.dropna(axis=1, how="any", inplace=True)


data_short = yf.download(tickers_string, start=start_short, interval='15m')
short_close = data_short["Close"]
short_volume = data_short["Volume"]
short_close.dropna(axis=0, how="all", inplace=True)
short_close.dropna(axis=1, how="any", inplace=True)
short_volume.dropna(axis=0, how="all", inplace=True)
short_volume.dropna(axis=1, how="any", inplace=True)

lcn = set(list(long_close))
lcv = set(list(long_volume))
scn = set(list(short_close))
scv = set(list(short_volume))
intersect = list(set.intersection(lcn, lcv, scn, scv))

train_long_close = long_close.loc[:str(midpoint.date()), intersect]
train_long_vol = long_volume.loc[:str(midpoint.date()), intersect]
test_long_close = long_close.loc[str(midpoint.date()):, intersect]
test_long_vol = long_volume.loc[str(midpoint.date()):, intersect]

train_short_close = short_close.loc[:str(midpoint.date()), intersect]
train_short_vol = short_volume.loc[:str(midpoint.date()), intersect]
test_short_close = short_close.loc[str(midpoint.date()):, intersect]
test_short_vol = short_volume.loc[str(midpoint.date()):, intersect]

print(train_short_close.index)
train_dataset = {
    'ticker':[],
    'intraday_close':[],
    'intraday_volume':[],
    'intraday_minutes':[],
    "mu_s":[],
    "mu_l":[],
    "std_s":[],
    "std_l":[],
    "skew_s":[],
    "skew_l":[],
    "kurt_s":[],
    "kurt_l":[],
    "ADF_s":[],
    "ADF_l":[],
    "H_s":[],
    "H_l":[],
    'daily_close':[],
    'daily_volume':[],
    'daily_minutes':[],
    'predict_close':[],
    'predict_volume':[],
    'predict_minutes':[]
}

for t in intersect:
    train_dataset['ticker'].append(t)

    d = train_short_close[t].values
    v = train_short_vol[t].values
    logr = np.log((d[1:] / d[:-1]))
    logv = np.log((v[1:] / v[:-1]))
    train_dataset['intraday_close'].append(logr.tostring())
    train_dataset['intraday_volume'].append(logv.tostring())
    times = train_short_close.index.to_pydatetime()
    tdelta = [((t - times[0]).days * 24 * 60) + ((t - times[0]).seconds // 60) for t in times]
    train_dataset['intraday_minutes'].append(np.array(tdelta).tostring())
    train_dataset['mu_s'].append(np.mean(d))
    train_dataset['std_s'].append(np.std(d))
    train_dataset['skew_s'].append(skew(d))
    train_dataset['kurt_s'].append(kurtosis(d))
    fuller = adfuller(logr)
    train_dataset['ADF_s'].append(fuller[0])
    H, c, _ = compute_Hc(d, kind='price', simplified=True)
    train_dataset['H_s'].append(H)

    d = train_long_close[t].values
    v = train_long_vol[t].values
    logr = np.log((d[1:] / d[:-1]))
    logv = np.log((v[1:] / v[:-1]))
    train_dataset['mu_l'].append(np.mean(d))
    train_dataset['std_l'].append(np.std(d))
    train_dataset['skew_l'].append(skew(d))
    train_dataset['kurt_l'].append(kurtosis(d))
    fuller = adfuller(logr)
    train_dataset['ADF_l'].append(fuller[0])
    H, c, _ = compute_Hc(d, kind='price', simplified=True)
    train_dataset['H_l'].append(H)

    train_dataset['daily_close'].append(logr.tostring())
    train_dataset['daily_volume'].append(logv.tostring())
    times = train_long_close.index.to_pydatetime()
    tdelta = [((t - times[0]).days * 24 * 60) + ((t - times[0]).seconds // 60) for t in times]
    train_dataset['daily_minutes'].append(np.array(tdelta).tostring())

    d = test_long_close[t].values
    v = test_long_vol[t].values
    logr = np.log((d[1:] / d[:-1]))
    logv = np.log((v[1:] / v[:-1]))
    train_dataset['predict_close'].append(logr.tostring())
    train_dataset['predict_volume'].append(logv.tostring())
    times = test_long_close.index.to_pydatetime()
    tdelta = [((t - times[0]).days * 24 * 60) + ((t - times[0]).seconds // 60) for t in times]
    train_dataset['predict_minutes'].append(np.array(tdelta).tostring())

training_dataset = pd.DataFrame(train_dataset)
training_dataset.set_index('ticker')

training_dataset.to_csv(str(midpoint.date()) + '.csv')