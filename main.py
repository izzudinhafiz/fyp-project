from fyptools import label_data as label
from fyptools import helper_functions as hf

import pandas as pd


tickers = hf.get_tickers(1)

for ticker in tickers:
    main_df = pd.read_csv("fixed_dataset/" + ticker + "_daily_adjusted.csv",
                          index_col="date", parse_dates=True)

    main_df["decision"] = label.return_label(main_df, 15, offset_type="simple")
    hf.plot_price_data(main_df, days=300, title="Simple Return Label", ticker=ticker)


