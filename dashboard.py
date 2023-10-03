import config, json
from iex import IEXStock
import pandas as pd
import yfinance as yf

tickers = pd.read_html(
    'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0].Symbol.to_list()

data = yf.download('AAPL', start='2010-01-01', interval='1mo')
# print(data.head())

def get_f_score(ticker='AAPL', years=20):
    stock = IEXStock(config.IEX_TOKEN, ticker)

    fundamentals = stock.get_fundamentals(last=years*4)
    df_f = pd.DataFrame(fundamentals)
    df_f.index = pd.to_datetime(df_f.reportDate)

    income_statement = stock.get_income_statement(last=years*4)
    df_is = pd.DataFrame(income_statement)
    df_is.index = pd.to_datetime(df_is.reportDate)

    balance_sheet = stock.get_balance_sheet(last=years*4)
    df_bs = pd.DataFrame(balance_sheet)
    df_bs.index = pd.to_datetime(df_bs.reportDate)

    cash_flow = stock.get_cash_flow(last=years*4)
    df_cf = pd.DataFrame(cash_flow)
    df_cf.index = pd.to_datetime(df_cf.reportDate)

    merged_df = pd.concat([df_f, df_is, df_bs, df_cf], axis=1)
    merged_df = merged_df.sort_index(ascending=True)
    merged_df = merged_df[~merged_df.index.duplicated(keep='first')]
    merged_df = merged_df.loc[:, ~merged_df.columns.duplicated()]
    merged_df['totalAssets_avg'] = merged_df.totalAssets.rolling(window=4).mean()

    merged_df['ROA'] = merged_df.netIncome.rolling(window=4).sum() / merged_df.totalAssets_avg
    merged_df['ΔROA'] = merged_df['ROA'].diff()
    merged_df['CFOA'] = merged_df.cashFlow / merged_df.totalAssets_avg
    merged_df['ACCRUAL'] = (merged_df.operatingIncome.rolling(window=4).sum() - merged_df.cashFlow.rolling(window=4).sum()) / merged_df.totalAssets_avg
    merged_df['ΔLEVER'] = (merged_df.longTermDebt / merged_df.totalAssets).diff()
    merged_df['ΔLIQUID'] = (merged_df.currentAssets / merged_df.totalCurrentLiabilities).diff()
    merged_df['EQ_OFFER'] = merged_df.sharesIssued.diff(periods=4)
    merged_df['ΔMARGIN'] = (merged_df.grossProfit / merged_df.totalRevenue).diff()
    merged_df['ΔTURN'] = (merged_df.totalRevenue / merged_df.totalAssets).diff()

    conditions = [
        (merged_df['ROA'] > 0),
        (merged_df['ΔROA'] > 0),
        (merged_df['CFOA'] > 0),
        (merged_df['ACCRUAL'] < 0),
        (merged_df['ΔLEVER'] < 0),
        (merged_df['ΔLIQUID'] < 0),
        (merged_df['EQ_OFFER'] <= 0),
        (merged_df['ΔMARGIN'] > 0),
        (merged_df['ΔTURN'] > 0)
    ]
    scores = [1, 1, 1, 1, 1, 1, 1, 1, 1]

    merged_df['F_SCORE'] = 0
    for condition, score in zip(conditions, scores):
        merged_df['F_SCORE'] = merged_df['F_SCORE'] + condition.astype(int) * score
    merged_df = merged_df.dropna(subset=['EQ_OFFER'])

    merged_df = merged_df.resample('M').first().shift(-1, freq='D')
    merged_df.index = merged_df.index + pd.DateOffset(months=1)
    merged_df = merged_df.resample('MS').first()
    merged_df = merged_df.ffill()
    merged_df = merged_df.rename(columns={'F_SCORE': ticker})

    return merged_df[ticker]

f_scores = []

for ticker in tickers[:10]:
    f_score = get_f_score(ticker)
    f_scores.append(f_score)

F_Scores = pd.DataFrame(f_scores).T
F_Scores.fillna(method='ffill', limit=10, inplace=True)

Price_Data = yf.download(tickers, F_Scores.index[0], F_Scores.index[-1] + pd.DateOffset(months=1) + pd.DateOffset(days=1),interval='1mo', auto_adjust=True)['Close']
