import math
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

df = pd.DataFrame({'a': [1, 3, 5, 7, 4, 5, 6, 4, 7, 8, 9],
                   'b': [3, 5, 6, 2, 4, 6, 7, 8, 7, 8, 9]})

reg = smf.ols('a ~ 1', data=df).fit(cov_type='HAC', cov_kwds={'maxlags': math.floor(4 * (len(df) / 100) ** (2 / 9))})
print(reg.summary())

intercept = np.ones_like(df['a'])

def Newey_West_t_stat(y, X):
    if isinstance(y, np.ndarray):
        y = np.array(y)
    # X = np.column_stack((np.ones(X.shape[0]), X))
    T = len(y)
    J = math.floor(4*(T/100)**(2/9))
    if X.ndim <= 1:
        beta = 1/(X.T @ X) * X.T @ y
        y_hat = X * beta
    else:
        beta = np.linalg.inv(X.T @ X) @ X.T @ y
        y_hat = X @ beta
    residuals = y - y_hat

    S0 = 0
    for t in range(1, T+1):
        if X.ndim <= 1:
            Xt = X[t - 1]
            S0 += residuals[t - 1] ** 2 * Xt * Xt.T
        else:
            Xt = X[t-1, :]
            S0 += residuals[t-1] ** 2 * Xt @ Xt.T

    S1 = 0
    for j in range(1, J+1):
        for t in range(j+1, T+1):
            if X.ndim <= 1:
                Xt = X[t - 1]
                Xtj = X[t - 1 - j]
                S1 += (1 - j / (1 + J)) * residuals[t - 1] * residuals[t - 1 - j] * (Xt * Xtj.T + Xtj * Xt.T)
            else:
                Xt = X[t - 1, :]
                Xtj = X[t - 1 - j, :]
                S1 += (1-j/(1+J))*residuals[t-1]*residuals[t-1-j]*(Xt @ Xtj.T + Xtj@Xt.T)
    S = S0/T + S1/T

    if X.ndim <= 1:
        V_ols = T * 1/(X.T @ X) * S * 1/(X.T @ X)
        return {'beta': beta, 'std err': np.sqrt(V_ols), 't-value': beta/np.sqrt(V_ols)}
    else:
        V_ols = T * np.linalg.inv(X.T@X)*S*np.linalg.inv(X.T@X)
        return {'beta': beta, 'std err': np.diag(np.sqrt(V_ols)), 't-value': beta / np.diag(np.sqrt(V_ols))}
