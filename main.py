from fyptools import label_data as label
from fyptools import helper_functions as hf
import pandas as pd
import fyptools.feature as feature
tickers = hf.get_tickers(1)

for ticker in tickers:
    main_df = pd.read_csv("fixed_dataset/" + ticker + "_daily_adjusted.csv",
                          index_col="date", parse_dates=True)

    print(feature.macd(main_df, (12,26)))
