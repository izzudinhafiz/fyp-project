import pandas as pd
from datetime import datetime
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
        self.years = int(end) - int(start) + 1
        self.history.record_daily_history()

    def get_price(self, ticker=None):
        return self.data[ticker].loc[self.date, "close"]

    def get_date(self):
        return self.date

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
        self.portfolio.annualized_return = (self.portfolio.equity / self.portfolio.starting_equity)**(1/self.years) - 1

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
        if ticker in self.positions.values():
            return True
        return False


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
                "units", "open_price", "close_price", "open_commission", "close_commission",
                "take_profit", "stop_loss", "close_type", "open_date", "close_date"]
        summary = pd.DataFrame(columns=cols)

        for identifier, position in self.positions.items():
            temp = {}
            temp["ticker"] = position.ticker
            temp["open_date"] = position.open_date
            temp["close_date"] = position.close_date
            temp["true_profit"] = position.true_profit
            temp["nominal_profit"] = position.nominal_profit
            temp["close_value"] = position.current_value
            temp["open_value"] = position.open_value
            temp["units"] = position.unit
            temp["open_price"] = position.open_price
            temp["close_price"] = position.current_price
            temp["open_commission"] = position.open_commission
            temp["close_commission"] = position.close_commission
            temp["take_profit"] = position.take_profit
            temp["stop_loss"] = position.stop_loss
            temp["close_type"] = position.close_type
            summary.loc[identifier] = temp
        summary.sort_index(inplace=True)
        return summary

    def get_position_summary_by_id(self, identifier):
        position = self.positions[identifier]
        temp = {}
        temp["ticker"] = position.ticker
        temp["open_date"] = position.open_date
        temp["close_date"] = position.close_date
        temp["true_profit"] = position.true_profit
        temp["nominal_profit"] = position.nominal_profit
        temp["close_value"] = position.current_value
        temp["open_value"] = position.open_value
        temp["units"] = position.unit
        temp["open_price"] = position.open_price
        temp["close_price"] = position.current_price
        temp["open_commission"] = position.open_commission
        temp["close_commission"] = position.close_commission
        temp["take_profit"] = position.take_profit
        temp["stop_loss"] = position.stop_loss
        temp["close_type"] = position.close_type
        return temp

    def get_position_summary_by_ticker(self, ticker):
        list_of_id = []
        for position in self.positions.values():
            if position.ticker == ticker:
                list_of_id.append(position.id)
        temp = {}
        if len(list_of_id) > 0:
            for identifier in list_of_id:
                temp[identifier] = self.get_position_summary_by_id(identifier)

        return temp

    def record_daily_history(self):
        portfolio = self.bt.portfolio
        daily = {"cash": portfolio.cash, "equity": portfolio.equity, "positions_value": portfolio.positions_value}
        self.daily_history[self.bt.get_date()] = daily

    def make_daily_history(self):
        self.daily_history = pd.DataFrame.from_dict(self.daily_history, orient="index")
