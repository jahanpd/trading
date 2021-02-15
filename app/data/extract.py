import numpy as np
import pandas as pd
import yfinance as yf
import datetime
import pytz
from statsmodels.tsa.stattools import adfuller
from hurst import compute_Hc, random_walk
from scipy.stats import skew, kurtosis
# from app.indicators.MaasoumiZaman import MZ

tickers = pd.read_csv('stake_tickers.csv')
# tickers = ["AAPL", "TSLA", "MSFT"]
tickers = list(tickers.Ticker.values)

start_long = datetime.datetime.now() - datetime.timedelta(days=180)
start_short = datetime.datetime.now() - datetime.timedelta(days=28)

midpoint_long = datetime.datetime.now() - datetime.timedelta(days=7)
midpoint_short = datetime.datetime.now() - datetime.timedelta(days=7)

data_short = yf.download("^GSPC", start=start_short, interval='30m')
data_long = yf.download("^GSPC", start=start_long)

long_train_index_close = data_long["Close"]
short_train_index_close = data_short["Close"]

# save index returns
index_dataset = {
    'ticker':[],
    'intraday_close':[],
    'daily_close':[],
}
d_idx = short_train_index_close.values.flatten()
logr_idx = np.log((d_idx[1:] / d_idx[:-1]))
d_idx_ = long_train_index_close.values.flatten()
logr_idx_ = np.log((d_idx[1:] / d_idx[:-1]))

index_dataset['ticker'].append("^GSPC")
index_dataset['intraday_close'].append(logr_idx.tobytes())
index_dataset['daily_close'].append(logr_idx_.tobytes())
index_dataset = pd.DataFrame(index_dataset)
index_dataset.to_csv(str(midpoint_long.date()) + '_index' + '.csv')

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
    'predict_minutes':[],
}

fundamentals = [
        'profitMargins',
        'enterpriseToEbitda',
        'forwardEps',
        'trailingEps',
        'bookValue',
        'priceToBook',
        'sharesPercentSharesOut',
        'heldPercentInstitutions',
        'heldPercentInsiders',
        'shortRatio',
        'shortPercentOfFloat',
        'pegRatio'
    ]
for f in fundamentals:
    train_dataset[f] = []

for t in tickers:
    try:
        data_short = yf.download(t, start=start_short, interval='30m')
        data_long = yf.download(t, start=start_long)
        short_close = data_short["Close"]
        short_volume = data_short["Volume"]
        long_close = data_long["Close"]
        long_volume = data_long["Volume"]
        train_long_close = long_close.loc[:str(midpoint_long.date())]
        train_long_vol = long_volume.loc[:str(midpoint_long.date())]
        train_short_close = short_close.loc[:str(midpoint_long.date())]
        train_short_vol = short_volume.loc[:str(midpoint_long.date())]


        test_long_close = long_close.loc[str(midpoint_long.date()):]


        d = train_short_close.values
        v = train_short_vol.values.astype(float)
        d[d == 0] = np.nan
        v[v == 0] = np.nan
        mask_d = ~(np.isnan(d) | np.isinf(d))
        mask_v = ~(np.isnan(v) | np.isinf(v))
        mask = mask_d & mask_v
        d_train_short = d[mask]
        v_train_short = v[mask]
        logr_train_short = np.log((d_train_short[1:] / d_train_short[:-1]))
        logv_train_short = np.log((v_train_short[1:] / v_train_short[:-1]))
        times = train_short_close.index.to_pydatetime()
        tdelta_train_short = np.array(
            [((t - times[0]).days * 24 * 60) + ((t - times[0]).seconds // 60) for t in times])[mask]
        fuller_train_short = adfuller(logr_train_short)
        H_train_short, c_train_short, _ = compute_Hc(d_train_short, kind='price', simplified=True)

        d = train_long_close.values
        v = train_long_vol.values.astype(float)
        d[d == 0] = np.nan
        v[v == 0] = np.nan
        mask_d = ~(np.isnan(d) | np.isinf(d))
        mask_v = ~(np.isnan(v) | np.isinf(v))
        mask = mask_d & mask_v
        d_train_long = d[mask]
        v_train_long = v[mask]
        logr_train_long = np.log((d_train_long[1:] / d_train_long[:-1]))
        logv_train_long = np.log((v_train_long[1:] / v_train_long[:-1]))
        fuller_train_long = adfuller(logr_train_long)
        H_train_long, c_train_long, _ = compute_Hc(d, kind='price', simplified=True)
        times = train_long_close.index.to_pydatetime()
        tdelta_train_long = np.array(
            [((t - times[0]).days * 24 * 60) + ((t - times[0]).seconds // 60) for t in times])[mask]

        d = test_long_close.values
        d[d == 0] = np.nan
        mask_d = ~(np.isnan(d) | np.isinf(d))
        mask = mask_d
        d_test_long = d[mask]
        logr_test_long = np.log((d_test_long[1:] / d_test_long[:-1]))
        times = test_long_close.index.to_pydatetime()
        tdelta_test_long = np.array(
            [((t - times[0]).days * 24 * 60) + ((t - times[0]).seconds // 60) for t in times])[mask]

        train_dataset['ticker'].append(t)

        train_dataset['intraday_close'].append(logr_train_short.tobytes())
        train_dataset['intraday_volume'].append(logv_train_short.tobytes())
        train_dataset['intraday_minutes'].append(np.array(tdelta_train_short).tobytes())
        train_dataset['mu_s'].append(np.mean(logr_train_short))
        train_dataset['std_s'].append(np.std(logr_train_short))
        train_dataset['skew_s'].append(skew(logr_train_short))
        train_dataset['kurt_s'].append(kurtosis(logr_train_short))
        train_dataset['ADF_s'].append(fuller_train_short[0])
        train_dataset['H_s'].append(H_train_short)


        train_dataset['mu_l'].append(np.mean(logr_train_long))
        train_dataset['std_l'].append(np.std(logr_train_long))
        train_dataset['skew_l'].append(skew(logr_train_long))
        train_dataset['kurt_l'].append(kurtosis(logr_train_long))
        train_dataset['ADF_l'].append(fuller_train_long[0])
        train_dataset['H_l'].append(H_train_long)
        train_dataset['daily_close'].append(logr_train_long.tobytes())
        train_dataset['daily_volume'].append(logv_train_long.tobytes())
        train_dataset['daily_minutes'].append(np.array(tdelta_train_long).tobytes())

        train_dataset['predict_close'].append(logr_test_long.tobytes())
        train_dataset['predict_minutes'].append(np.array(tdelta_test_long).tobytes())

        # get fundamentals
        ticker_object = yf.Ticker(t)
        fund = ticker_object.info
        
        for f in fundamentals:
            try:
                train_dataset[f].append(float(fund[f]))
            except Exception:
                print("no fundamentals")
                train_dataset[f].append(np.nan)
    except Exception:
        print("failed ", t, Exception)

for key in train_dataset:
    print(len(train_dataset[key]))

training_dataset = pd.DataFrame(train_dataset)
training_dataset.set_index('ticker')

training_dataset.to_csv(str(midpoint_long.date()) + '.csv')

print(training_dataset)