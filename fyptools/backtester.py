import pandas as pd
import os
import matplotlib.pyplot as plt
import datetime
"""
Template for running Backtester
- Initialize Backtester
- Loop for i in range(len(bt.dates) - 1)
    - Compute and Perform orders
    - Backtester.next_day()
- Backtester.end_of_simulation()
"""


class Backtester(object):
    def __init__(self, world_data: pd.DataFrame, cash, start, end):
        self.data = world_data
        self.dates = world_data[start:end].index.tolist()
        self.tickers = list(set(world_data.columns.get_level_values(0)))
        self.counter = 0
        self.date = self.dates[self.counter]
        self.portfolio = Portfolio(self, cash)
        self.history = History(self)
        self.commission_rate = 0.01
        self.start_date = self.dates[0].to_pydatetime()
        self.end_date = self.dates[-1].to_pydatetime()
        self.history.record_daily_history()
        _ = pd.read_csv(r"{}\fyptools\data\daily_adjusted_SPX.csv".format(os.path.abspath(os.curdir)),
                        index_col="date", parse_dates=True).sort_index()
        self.benchmark_data = _.loc[pd.to_datetime(self.dates[0]).date():pd.to_datetime(self.dates[-1]).date()]

    def get_price(self, ticker=None):
        return self.data[ticker].loc[self.date, "close"]

    def get_date(self, date_format="pandas"):
        if date_format == "pandas":
            return self.date
        elif date_format == "python":
            return self.date.to_pydatetime()

    def next_day(self):
        self.counter += 1
        self.date = self.dates[self.counter]
        self.portfolio.update_positions()
        self.history.record_daily_history()

    def end_of_simulation(self):
        # Close all positions
        for position in self.portfolio.positions.values():
            position.manually_close("eos")
        self.portfolio.update_positions()

        # Make one last history
        self.date = self.date + pd.DateOffset(1)
        self.history.record_daily_history()
        self.history.make_daily_history()

        # Update records for report
        years = self.end_date.year - self.start_date.year + 1
        self.portfolio.annualized_return = (self.portfolio.equity / self.portfolio.starting_equity)**(1/years) - 1

    def has_data(self, ticker):
        if str(self.data[ticker].loc[self.date, "close"]) != "nan":
            return True
        else:
            return False


class Portfolio(object):
    def __init__(self, backtester, cash):
        self.cash = cash
        self.equity = cash
        self.counter = 0
        self.positions = {}
        self.long_positions = []
        self.short_positions = []
        self.to_close = []
        self.bt = backtester
        self.long_equity = 0
        self.short_equity = 0
        self.positions_value = 0
        self.starting_equity = self.equity
        self.annualized_return = None

    def update_positions(self):
        self.positions_value = 0
        self.to_close.clear()
        for identifier, position in self.positions.items():
            position.update_position()
            if position.check_close():
                position.close()
                self.to_close.append(identifier)
            if identifier not in self.to_close:
                self.positions_value += position.current_value

        if len(self.to_close) > 0:
            for identifier in self.to_close:
                self.cash += self.positions[identifier].close_value - (self.positions[identifier].nominal_profit
                                                                       - self.positions[identifier].true_profit)
                if self.positions[identifier].type == "long":
                    self.long_positions.remove(identifier)
                elif self.positions[identifier].type == "short":
                    self.short_positions.remove(identifier)
                self.bt.history.record_position(identifier)
                self.positions.pop(identifier)
        self.equity = self.cash + self.positions_value

    def open_position_value(self, ticker, value, tp=None, sl=None):
        self.positions[self.counter] = Position(self.bt, self, self.counter, ticker, value, tp, sl)

        if self.positions[self.counter].type == "long":
            self.long_positions.append(self.counter)
        elif self.positions[self.counter].type == "short":
            self.short_positions.append(self.counter)

        self.cash -= value
        self.positions_value += value
        self.counter += 1

    def open_position_unit(self, ticker, unit, tp=None, sl=None):
        value = self.bt.get_price(ticker) * unit
        self.open_position_value(ticker, value, tp, sl)

    def is_open(self, ticker):
        identifier = []
        for position in self.positions.values():
            if position.ticker == ticker:
                identifier.append(position.id)

        if len(identifier) == 1:
            return True
        elif len(identifier) > 1:
            return identifier
        else:
            return False

    def open_type(self, ticker):
        for position in self.positions.values():
            if position.ticker == ticker:
                return position.type

        return None

    def get_id(self, ticker):
        for position in self.positions.values():
            if position.ticker == ticker:
                return position.id

        return None


class Position(object):
    def __init__(self, backtester, portfolio, identifier,
                 ticker, value, tp, sl):
        self.bt = backtester
        self.portfolio = portfolio
        self.id = identifier
        self.ticker = ticker
        self.open_price = self.bt.get_price(self.ticker)
        self.open_value = value
        self.unit = self.open_value / self.open_price
        self.open_date = self.bt.get_date()
        self.take_profit = tp
        self.stop_loss = sl
        self.open_commission = abs(self.bt.commission_rate * self.open_value)
        self.force_close = False
        if self.open_value < 0:
            self.type = "short"
        else:
            self.type = "long"

        # To be updated every day
        self.current_price = self.open_price
        self.current_value = value
        self.nominal_profit = self.current_value - self.open_value
        self.true_profit = self.nominal_profit - self.open_commission
        self.daily_change = 0

        # To be updated when closed (also true_profit)
        self.close_commission = None
        self.close_date = None
        self.close_type = None
        self.close_price = None
        self.close_value = None

    def update_position(self):
        self.current_price = self.bt.get_price(self.ticker)
        self.current_value = self.unit * self.current_price
        self.daily_change = self.current_value - self.open_value - self.nominal_profit
        self.nominal_profit = self.current_value - self.open_value
        self.true_profit = self.nominal_profit - self.open_commission

    def close(self):
        self.close_commission = abs(self.current_value * self.bt.commission_rate)
        self.close_date = self.bt.get_date()
        self.true_profit = self.nominal_profit - self.open_commission - self.close_commission
        self.close_price = self.current_price
        self.close_value = self.current_value
        self.current_value = None
        self.current_price = None

        return self.id

    def check_close(self):
        if self.force_close:
            return True
        elif self.take_profit is not None or self.stop_loss is not None:
            if self.type == "long":
                if self.take_profit is not None:
                    if self.current_price >= self.take_profit:
                        self.close_type = "tp"
                        return True
                if self.stop_loss is not None:
                    if self.current_price <= self.stop_loss:
                        self.close_type = "sl"
                        return True
            elif self.type == "short":
                if self.take_profit is not None:
                    if self.current_price <= self.take_profit:
                        self.close_type = "tp"
                        return True
                if self.stop_loss is not None:
                    if self.current_price >= self.stop_loss:
                        self.close_type = "sl"
                        return True
            return False
        else:
            return False

    def manually_close(self, reason=None):
        self.force_close = True
        if reason is None:
            self.close_type = "manual"
        else:
            self.close_type = reason


class History(object):
    def __init__(self, backtester):
        self.daily_history = {}
        self.positions = {}
        self.bt = backtester

    def record_position(self, identifier):
        self.positions[identifier] = self.bt.portfolio.positions[identifier]

    def get_summary(self):
        cols = ["ticker",  "true_profit", "nominal_profit", "close_value", "open_value",
                "unit", "open_price", "close_price", "open_commission", "close_commission",
                "take_profit", "stop_loss", "close_type", "open_date", "close_date"]
        index = self.positions.keys()
        data = []
        for identifier in index:
            position = self.positions[identifier]
            temp = []
            for col in cols:
                temp.append(getattr(position, col))
            data.append(temp)

        return pd.DataFrame(data, index, cols)

    def get_position_summary_by_id(self, identifier):
        cols = ["ticker",  "true_profit", "nominal_profit", "close_value", "open_value",
                "unit", "open_price", "close_price", "open_commission", "close_commission",
                "take_profit", "stop_loss", "close_type", "open_date", "close_date"]
        position = self.positions[identifier]
        data = []
        for col in cols:
            data.append(getattr(position, col))

        return pd.Series(data, cols)

    def get_position_summary_by_ticker(self, ticker):
        list_of_id = []
        for position in self.positions.values():
            if position.ticker == ticker:
                list_of_id.append(position.id)
        temp = {}
        if len(list_of_id) > 0:
            for identifier in list_of_id:
                temp[identifier] = self.get_position_summary_by_id(identifier)

        return pd.DataFrame(temp).transpose()

    def record_daily_history(self):
        portfolio = self.bt.portfolio
        cols = ["cash", "equity", "positions_value"]
        daily = {}
        for col in cols:
            daily[col] = getattr(portfolio, col)
        self.daily_history[self.bt.get_date()] = daily

    def make_daily_history(self):
        self.daily_history = pd.DataFrame.from_dict(self.daily_history, orient="index")

    def report(self):
        data = dict()
        data["annualized_return"] = self.bt.portfolio.annualized_return
        data["beta"] = None
        data["alpha"] = None
        data["average_net_exposure"] = None

        return data

    def return_report(self):
        pass

    def plot_history(self):
        portfolio_return = self.daily_history["equity"]
        portfolio_return = portfolio_return / portfolio_return[0]
        index_return = self.bt.benchmark_data["close"]
        index_return = index_return / index_return[0]

        plt.plot(portfolio_return, label="Portfolio")
        plt.plot(index_return, label="Benchmark - SPX")
        plt.legend()
        plt.show()
