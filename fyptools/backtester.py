
class Backtester(object):
    def __init__(self, data, equity):
        self.counter = 0
        self.dates = data.index.tolist()
        self.date = self.dates[self.counter]
        self.equity = equity
        self.positions = {}
        self.portfolio = {"equity": self.equity}
        self.ticker = {"AAPL": Symbol(data, self.date)}
        self.history = {}

    def next_day(self):
        self.counter += 1
        self.date = self.dates[self.counter]

        for ticker, symbol in self.ticker.items():
            symbol.update_price(self.date)

        for position in self.positions.values():
            position.update_next_day()

    def buy_value(self, ticker, value):
        if ticker not in self.positions.keys():
            self.positions[ticker] = Agent(ticker, self.date, self)
        self.positions[ticker].order(value)

    def buy_unit(self, ticker, units):
        value = self.ticker[ticker].price * units
        self.buy_value(ticker, value)


class Agent(object):
    def __init__(self, ticker, date, other):
        self.name = ticker
        self.bt = other
        self.open_date = date
        self.close_date = None
        self.open_value = None
        self.unit = None
        self.current_value = None
        self.profit = None
        self.close_value = None

    def order(self, amount):
        current_price = self.bt.ticker[self.name].price
        self.open_value = amount
        self.unit = self.open_value / current_price
        self.current_value = self.open_value

    def update_next_day(self):
        self.current_value = self.bt.ticker[self.name].price * self.unit
        self.profit = self.current_value - self.open_value


class Symbol(object):
    def __init__(self, data, date):
        self.prices = data["close"]
        self.price = self.prices[date]

    def update_price(self, date):
        self.price = self.prices[date]