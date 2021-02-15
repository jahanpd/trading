import numpy as np
import pandas as pd
from scipy.stats import skew, kurtosis
from statsmodels.tsa.stattools import pacf
from statsmodels.tsa.stattools import adfuller
from hurst import compute_Hc, random_walk
# https://towardsdatascience.com/how-the-mathematics-of-fractals-can-help-predict-stock-markets-shifts-19fee5dd6574
# takes pandas df of close prices
def metrics(prices_series):
    tickers = list(prices_series)
    data = {}
    m = {
        "mu":{},
        "std":{},
        "skew":{},
        "kurt":{},
        "ADF":{},
        "H":{}
    }
    for t in tickers:
        stats = {}
        dat = {}
        d = prices_series[t].values
        mask = ~np.isnan(d)
        logr = np.log((d[1:] / d[:-1]))
        logr = logr[~np.isnan(logr)]
        logr = logr[~np.isinf(logr)]
        dat["data"] = logr.tolist()
        m["mu"][t] = np.mean(logr[-30:])
        m["std"][t] = np.std(logr[-30:])
        m["skew"][t] = skew(logr[-30:])
        m["kurt"][t] = kurtosis(logr[-30:])
        ac = pacf(logr, nlags=min(int(10 * np.log10(len(logr))), len(logr) // 2 - 1) )
        dat["autocorrelation"] = ac
        fuller = adfuller(logr)
        m["ADF"][t] = fuller[0]
        # calculate hurst exponential
        try:
            H, c, _ = compute_Hc(d[mask], kind='price', simplified=True)
        except Exception as e:
            H, c = np.nan, np.nan
        m["H"][t] = H
        data[t] = dat
    return m, data

