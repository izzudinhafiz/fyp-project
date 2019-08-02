import pandas as pd
import numpy as np


def sma(data: pd.DataFrame, period: int, *columns: str):
    frame = data.copy()
    column_list = []

    if len(columns) == 0:
        columns_to_calculate = ["close"]
    else:
        columns_to_calculate = columns

    for column in columns_to_calculate:
        series = frame[column].copy()
        column_name = str(column) + "_SMA_" + str(period)
        column_list.append(column_name)
        frame[column_name] = series.rolling(period).mean()

    return frame[column_list]


def ema(data: pd.DataFrame, period: int, *columns):
    frame = data.copy()
    column_list = []

    if len(columns) == 0:
        columns_to_calculate = ["close"]
    else:
        columns_to_calculate = columns

    for column in columns_to_calculate:
        series = frame[column].copy()
        column_name = str(column) + "_EMA_" + str(period)
        column_list.append(column_name)
        frame[column_name] = series.ewm(span=period, min_periods=period).mean()

    return frame[column_list]


def macd(data: pd.DataFrame, period: tuple = (12, 26)):
    if type(period) != tuple:
        raise TypeError("Period should be of type tuple")
    if len(period) > 2:
        raise ValueError("Period should be a tuple of length 2")

    frame = data.copy()
    period_1_name: str = "close_EMA_{}".format(period[0])
    period_2_name: str = "close_EMA_{}".format(period[1])
    if period_1_name not in frame.columns:
        frame[period_1_name] = ema(frame, period[0])
    if period_2_name not in frame.columns:
        frame[period_2_name] = ema(frame, period[1])

    frame["MACD"] = frame[period_1_name] - frame[period_2_name]

    return frame["MACD"]


def rsi(data: pd.DataFrame):
    pass


def bollinger_band(data: pd.DataFrame):
    pass
