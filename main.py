import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import config, json
from iex_data import IEXStock
import pandas as pd
import yfinance as yf
import itertools
from newey_west import Newey_West

tickers = pd.read_csv('Data/mid-mega_stocks.csv')

class Stock:
    def __init__(self, symbol):
        self.symbol = symbol
        self.stock = IEXStock(config.IEX_TOKEN, 'AAPL')
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
        merged_df['ACCRUAL'] = (merged_df.operatingIncome.rolling(window=4).sum() - merged_df.cashFlow.rolling(
            window=4).sum()) / merged_df.totalAssets_avg
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
        merged_df['F_SCORE_avg'] = merged_df['F_SCORE'].rolling(4).mean()

        merged_df = merged_df.resample('M').first().shift(-1, freq='D')
        merged_df.index = merged_df.index + pd.DateOffset(months=1)
        merged_df = merged_df.resample('MS').first()
        merged_df = merged_df.ffill()
        merged_df = merged_df.rename(columns={'F_SCORE_avg': ticker})

        return merged_df[ticker]

    def get_netAssets(self):
        bs = self.balance_sheet.copy()
        bs = bs.resample('M').first().shift(-1, freq='D')
        bs.index = bs.index + pd.DateOffset(months=1)
        bs = bs.resample('MS').first()
        bs = bs.ffill()
        bs = bs.rename(columns={'netTangibleAssets': ticker})
        return bs[ticker]


f_scores = []
# with open('f_scores.pkl', 'rb') as f:
#     f_scores = pickle.load(f)
for ticker in tickers.Symbol.to_list()[:]:
    print(ticker)
    try:
        stock = Stock(symbol=ticker)
        f_score = stock.get_f_score()
        f_scores.append(f_score)
    except Exception as e:
        print(e)


F_Scores = pd.read_csv('Data/All_F_Scores.csv', index_col=0, parse_dates=True)
# F_Scores = pd.DataFrame(f_scores).T
F_Scores.fillna(method='ffill', limit=10, inplace=True)
F_Scores = F_Scores.loc['2013-06-01':'2023-06-01']

# nan_counts = F_Scores.isna().sum(axis=1)

Price_Data = yf.download(F_Scores.columns.to_list(), F_Scores.index[0] - pd.DateOffset(months=2), F_Scores.index[-1] +
                         pd.DateOffset(months=1) + pd.DateOffset(days=1), interval='1mo', auto_adjust=True)['Close']
# Price_Data = Price_Data[Price_Data.index.day == 1]

Returns = Price_Data.pct_change().shift(1)
Returns = Returns.loc['2013-06-01':'2023-07-01']

# Group_F = ['Low', 'Middle', 'High']
Group_F = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
Group_S = ['Loser', 'P2', 'P3', 'P4', 'Winner']
combinations = list(itertools.product(Group_F, Group_S))
Group_Return = {combo: [] for combo in combinations}
filter_price = 5

for i in range(len(Returns) - 1):
    str_stocks_dict = {}
    str_groups = pd.qcut(Returns.iloc[i][Price_Data.iloc[i]>filter_price], 5, labels=Group_S)
    grouped_stocks = Returns.iloc[i][Price_Data.iloc[i]>filter_price].groupby(str_groups)
    for group, stocks in grouped_stocks:
        str_stocks_dict[group] = stocks.index.tolist()

    f_stocks_dict = {}
    # bins = [-1, 3, 6, 9]
    # f_groups = pd.cut(F_Scores.iloc[i][Price_Data.iloc[i]>filter_price], bins, labels=Group_F)
    # grouped_stocks = F_Scores.iloc[i][Price_Data.iloc[i]>filter_price].groupby(f_groups)
    # for group, stocks in grouped_stocks:
    #     f_stocks_dict[group] = stocks.index.tolist()
    for j in range(len(Group_F)):
        f_stocks_dict[Group_F[j]] = F_Scores.iloc[i][Price_Data.iloc[i]>filter_price].index[F_Scores.iloc[i][Price_Data.iloc[i]>filter_price]==j].tolist()

    f_stocks_df = pd.DataFrame.from_dict(f_stocks_dict, orient='index').transpose()
    str_stocks_df = pd.DataFrame.from_dict(str_stocks_dict, orient='index').transpose()

    f_stocks_df = f_stocks_df.melt(var_name='Group', value_name='Stock').dropna()
    str_stocks_df = str_stocks_df.melt(var_name='Group', value_name='Stock').dropna()

    merged_df = pd.merge(f_stocks_df, str_stocks_df, on='Stock', how='outer', suffixes=('_F', '_S'))
    merged_df.reset_index(drop=True, inplace=True)
    merged_df = merged_df.dropna()

    for combo in combinations:
        group_f, group_s = combo
        groups = merged_df['Stock'][(merged_df['Group_F'] == group_f) & (merged_df['Group_S'] == group_s)].to_list()
        Group_Return[combo].append(Returns.iloc[i+1][groups].mean())

mean_values = {key: np.mean([x for x in value if x is not np.nan]) for key, value in Group_Return.items()}
values = np.array(list(mean_values.values()))*100
values = values.reshape((10, 5)).T

left_minus_right = values[:, 2] - values[:, 0]
new_values = np.column_stack((values, left_minus_right))

low_minus_winner = values[0, :] - values[4, :]
new_values = np.row_stack((new_values, np.append(low_minus_winner, [np.nan])))

plt.figure(figsize=(10, 6))
heatmap = sns.heatmap(new_values, annot=True, fmt=".3f", cmap="YlGnBu", xticklabels=Group_F + ['H-L'], yticklabels=Group_S + ['L-W'], cbar=False)
heatmap.xaxis.tick_top()
plt.title('Raw Return')
plt.xlabel('F_score', labelpad=20)
plt.gca().xaxis.set_label_coords(-0.01, +1.05)
plt.ylabel('Past 1-month performance')
plt.show()

T_stat = {}
for combo in combinations:
    y = np.array(Group_Return[combo])
    y = np.nan_to_num(y, nan=0)
    T_stat[combo] = Newey_West(y, np.ones_like(y))['t-value']
    # plt.plot((1+pd.Series(Group_Return[combo], index=F_Scores.index[:-1])).cumprod(), label=combo)
    # plt.legend()
    # plt.show()
    # plt.pause(1)

values2 = np.array(list(T_stat.values()))
values2 = values2.reshape((10, 5)).T


plt.figure(figsize=(10, 6))
sns.heatmap(values2, annot=True, fmt=".3f", cmap="YlGnBu", xticklabels=Group_F, yticklabels=Group_S, cbar=False)
plt.title('Newey-West Adjusted t-value')
plt.xlabel('F_score')
plt.ylabel('Past 1month performance')
plt.show()


## single sort by F-score


Group_F = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
Group_Return = {combo: [] for combo in Group_F}
filter_price = 5

for i in range(len(Returns) - 1):

    f_stocks_dict = {}
    for j in range(len(Group_F)):
        f_stocks_dict[Group_F[j]] = F_Scores.iloc[i][Price_Data.iloc[i]>filter_price].index[F_Scores.iloc[i][Price_Data.iloc[i]>filter_price]==j].tolist()

    f_stocks_df = pd.DataFrame.from_dict(f_stocks_dict, orient='index').transpose()
    f_stocks_df = f_stocks_df.melt(var_name='Group', value_name='Stock').dropna()
    f_stocks_df.reset_index(drop=True, inplace=True)
    f_stocks_df = f_stocks_df.dropna()

    for score in Group_F:
        groups = f_stocks_df['Stock'][f_stocks_df['Group'] == score]
        Group_Return[score].append(Returns.iloc[i+1][groups].mean())

mean_values = {key: np.mean([x for x in value if x is not np.nan]) for key, value in Group_Return.items()}
values = np.array(list(mean_values.values()))*100
values = values.reshape((10, 1)).T

T_stat = {}
for combo in Group_F:
    y = np.array(Group_Return[combo])
    y = np.nan_to_num(y, nan=0)
    T_stat[combo] = Newey_West(y, np.ones_like(y))['t-value']