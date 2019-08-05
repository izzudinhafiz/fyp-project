import pandas as pd
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
        self.counter = 0
        self.date = self.dates[self.counter]
        self.portfolio = Portfolio(self, cash)
        self.history = History(self)
        self.commission_rate = 0.01

    def get_price(self, ticker=None):
        if ticker is not None:  # not implemented yet
            return self.data[ticker].loc[self.date, "close"]
        return self.data.close[self.date]

    def get_date(self):
        return self.date

    def next_day(self):
        self.counter += 1
        self.date = self.dates[self.counter]
        self.portfolio.update_positions()

    def end_of_simulation(self):
        for position in self.portfolio.positions.values():
            position.manually_close("eos")
        self.portfolio.update_positions()


class Portfolio(object):
    def __init__(self, backtester, cash):
        self.cash = cash
        self.equity = cash
        self.counter = 0
        self.positions = {}
        self.to_close = []
        self.bt = backtester

    def update_positions(self):
        for identifier, position in self.positions.items():
            position.update_position()
            if position.check_close():
                position.close()
                self.to_close.append(identifier)

        if len(self.to_close) > 0:
            for identifier in self.to_close:
                self.cash += self.positions[identifier].true_profit
                self.bt.history.add(identifier)
                self.positions.pop(identifier)

        self.to_close.clear()

    def open_position_value(self, ticker, value, tp=None, sl=None):
        self.positions[self.counter] = Position(self.bt, self, self.counter, ticker, value, tp, sl)
        self.cash -= value
        self.counter += 1

    def open_position_unit(self, ticker, unit, tp=None, sl=None):
        value = self.bt.get_price() * unit
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
        self.open_price = self.bt.get_price()
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

        # To be updated when closed (also true_profit)
        self.close_commission = 0
        self.close_date = None
        self.close_type = None

    def update_position(self):
        self.current_price = self.bt.get_price()
        self.current_value = self.unit * self.current_price
        self.nominal_profit = self.current_value - self.open_value
        self.true_profit = self.nominal_profit - self.open_commission

    def close(self):
        self.close_commission = abs(self.current_value * self.bt.commission_rate)
        self.close_date = self.bt.get_date()
        self.true_profit = self.nominal_profit - self.open_commission - self.close_commission
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
        self.positions = {}
        self.bt = backtester

    def add(self, identifier):
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
