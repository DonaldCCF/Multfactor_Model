import requests


class IEXStock:

    def __init__(self, token, symbol, environment='production'):
        if environment == 'production':
            self.BASE_URL = 'https://cloud.iexapis.com/v1'
        else:
            self.BASE_URL = 'https://sandbox.iexapis.com/v1'

        self.token = token
        self.symbol = symbol

    def get_logo(self):
        url = f"{self.BASE_URL}/stock/{self.symbol}/logo?token={self.token}"
        r = requests.get(url)

        return r.json()

    def get_company_info(self):
        url = f"{self.BASE_URL}/stock/{self.symbol}/company?token={self.token}"
        r = requests.get(url)

        return r.json()

    def get_company_news(self, last=10):
        url = f"{self.BASE_URL}/stock/{self.symbol}/news/last/{last}?token={self.token}"
        r = requests.get(url)

        return r.json()

    def get_stats(self):
        url = f"{self.BASE_URL}/stock/{self.symbol}/advanced-stats?token={self.token}"
        r = requests.get(url)

        return r.json()

    def get_fundamentals(self, period='quarterly', last=4):
        url = f"{self.BASE_URL}/time-series/fundamentals/{self.symbol}/{period}?last={last}&token={self.token}"
        r = requests.get(url)

        return r.json()

    def get_income_statement(self, period='quarterly', last=4):
        url = f"{self.BASE_URL}/time-series/income/{self.symbol}/{period}?last={last}&token={self.token}"
        r = requests.get(url)

        return r.json()

    def get_balance_sheet(self, period='quarterly', last=4):
        url = f"{self.BASE_URL}/time-series/balance_sheet/{self.symbol}/{period}?last={last}&token={self.token}"
        r = requests.get(url)

        return r.json()

    def get_cash_flow(self, period='quarterly', last=4):
        url = f"{self.BASE_URL}/time-series/cash_flow/{self.symbol}/{period}?last={last}&token={self.token}"
        r = requests.get(url)

        return r.json()

    def get_fundamental_valuations(self, frequency='ttm', last=4):
        url = f"{self.BASE_URL}/time-series/fundamental_valuations/{self.symbol}/{frequency}?last={last}&token={self.token}"
        r = requests.get(url)

        return r.json()

    def get_dividends(self, range='5y'):
        url = f"{self.BASE_URL}/stock/{self.symbol}/dividends/{range}?token={self.token}"
        r = requests.get(url)

        return r.json()

    def get_institutional_ownership(self):
        url = f"{self.BASE_URL}/stock/{self.symbol}/institutional-ownership?token={self.token}"
        r = requests.get(url)

        return r.json()

    def get_insider_transactions(self):
        url = f"{self.BASE_URL}/stock/{self.symbol}/insider-transactions?token={self.token}"
        r = requests.get(url)

        return r.json()
