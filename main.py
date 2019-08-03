from fyptools import label_data as label
from fyptools import helper_functions as hf
import pandas as pd
import fyptools.feature as feature
import time
tickers = hf.get_tickers(1)

for ticker in tickers:
    main_df = pd.read_csv("fixed_dataset/" + ticker + "_daily_adjusted.csv",
                          index_col="date", parse_dates=True)
    main_df["macd"] = feature.macd(main_df)
    main_df["rsi"] = feature.rsi(main_df)
    main_df["bb_mid"], main_df["bb_up"], main_df["bb_low"] = feature.bollinger_band(main_df)
    print(main_df[["close", "macd", "rsi", "bb_mid", "bb_up", "bb_low"]])
