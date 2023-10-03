import config, json
from iex import IEXStock
import pandas as pd
import yfinance as yf

tickers = pd.read_html(
    'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0].Symbol.to_list()

data = yf.download('AAPL', start='2010-01-01', interval='1mo')
# print(data.head())

class Stock:
    def __init__(self, symbol):
        self.symbol = symbol
        self.stock = IEXStock(config.IEX_TOKEN, self.symbol)
        self.fundamentals = self.stock.get_fundamentals()
        self.income_statement = self.stock.get_income_statement()
        self.balance_sheet = self.stock.get_balance_sheet()
        self.cash_flow = self.stock.get_cash_flow()

    def get_f_score(self):
        merged_df = pd.concat([self.fundamentals, self.income_statement, self.balance_sheet, self.cash_flow], axis=1)
        merged_df = merged_df.sort_index(ascending=True)
        merged_df = merged_df[~merged_df.index.duplicated(keep='first')]
        merged_df = merged_df.loc[:, ~merged_df.columns.duplicated()]
        merged_df = merged_df.copy()
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

    def get_netAssets(self):
        bs = self.balance_sheet.copy()
        bs = bs.resample('M').first().shift(-1, freq='D')
        bs.index = bs.index + pd.DateOffset(months=1)
        bs = bs.resample('MS').first()
        bs = bs.ffill()
        bs = bs.rename(columns={'netTangibleAssets': ticker})
        return bs

f_scores = []
netAssets = []

for ticker in tickers[:10]:
    stock = Stock(symbol=ticker)
    f_score = stock.get_f_score()
    netAsset = stock.get_netAssets()
    f_scores.append(f_score)
    netAssets.append(netAsset)

F_Scores = pd.DataFrame(f_scores).T
F_Scores.fillna(method='ffill', limit=10, inplace=True)

Price_Data = yf.download(tickers, F_Scores.index[0], F_Scores.index[-1] + pd.DateOffset(months=1) + pd.DateOffset(days=1),interval='1mo', auto_adjust=True)['Close']
