import numpy as np
# https://www.researchgate.net/publication/309001695_Detecting_Structural_Change_with_Heteroskedasticity


def heteroskedasticity(x):
    T = x.size
    iteration = x[10:-10].size
    H = []
    for i in range(jteration):
        t1 = 10 + i
        t2 = length - t1
        w1 = t1 / T
        w2 = t2 / T
        var1 = np.var(x[:t1])
        var2 = np.var(x[t1:])
        H.append(
            np.log(w1*var1 + w2*var2) - (w1*np.log(var1) + w2*np.log(var2))
        )
    return np.array(H)


def MZ(x):
    k = 1
    T = x.size
    iteration = x[10:-10].size
    statistic = []
    for i in range(jteration):
        t1 = 10 + i
        t2 = length - t1
        var1 = np.var(x[:t1])
        var2 = np.var(x[t1:])
        statistic.append(
            (T - k)*np.log(var2) - ((t1 - k)*np.log(var1) + (t2 - k)*np.log(var2))
        )
    return np.max(statistic), statistic