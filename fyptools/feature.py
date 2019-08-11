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


def volatility_sd(data: pd.DataFrame, period: int):
    frame = data.copy()

    return frame.close.rolling(period).std(ddof=0)


def macd(data: pd.DataFrame, period: tuple = (12, 26)):
    if type(period) != tuple:
        raise TypeError("Period should be of type tuple, given {} instead".format(type(period)))
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


def rsi(data: pd.DataFrame, period: int = 14):
    """
                     100
    RSI = 100 - --------
                 1 + RS

    RS = Average Gain / Average Loss

    First Average Gain = Sum of Gains over the past 14 periods / 14.
    First Average Loss = Sum of Losses over the past 14 periods / 14

    Average Gain = [(previous Average Gain) x 13 + current Gain] / 14.
    Average Loss = [(previous Average Loss) x 13 + current Loss] / 14.
    """

    frame = data.copy()

    changes = frame.close - frame.close.shift(1)
    gains, losses = changes.copy(), changes.copy()
    gains.loc[gains < 0] = 0
    losses.loc[losses > 0] = 0
    losses = losses.abs()

    gains, losses = np.asarray(gains), np.asarray(losses)

    first_gain = np.sum(gains[1:period+1]) / period
    first_loss = np.sum(losses[1:period+1]) / period

    avg_gain, avg_loss = np.zeros(len(gains)), np.zeros(len(losses))
    avg_gain[avg_gain == 0] = np.nan
    avg_loss[avg_loss == 0] = np.nan

    for i in range(len(changes) - period):
        if i == 0:
            avg_gain[i+period] = first_gain
            avg_loss[i+period] = first_loss
        else:
            avg_gain[i+period] = (avg_gain[i+period - 1] * (period - 1) + gains[i+period]) / period
            avg_loss[i + period] = (avg_loss[i + period - 1] * (period - 1) + losses[i + period]) / period

    RS = avg_gain / avg_loss
    RSI = 100 - (100 / (1 + RS))

    return RSI


def bollinger_band(data: pd.DataFrame):
    '''
    * Middle Band = 20-day simple moving average (SMA)
    * Upper Band = 20-day SMA + (20-day standard deviation of price x 2)
    * Lower Band = 20-day SMA - (20-day standard deviation of price x 2)

    :param data: Pandas DataFrame containing OHLC data
    :return: middle_band, upper_band, lower_band
    '''

    frame = data.copy()
    sd = volatility_sd(frame, 20).to_numpy()
    middle_band = sma(frame, 20).to_numpy().reshape(-1)
    upper_band = middle_band + (sd * 2)
    lower_band = middle_band - (sd * 2)

    return middle_band, upper_band, lower_band

