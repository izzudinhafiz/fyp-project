from fyptools import label_data as label
from fyptools import helper_functions as hf
import pandas as pd

tickers = hf.get_tickers(3)

for ticker in tickers:
    main_df = pd.read_csv("fixed_dataset/" + ticker + "_daily_adjusted.csv",
                          index_col="date", parse_dates=True)

    main_df["decision"] = label.rto_label(main_df, offset=15)
    main_df["decision"] = label.cleanup_region_agreement(main_df)
    hf.plot_price_data(main_df, days=500, title="RTO Label (Region Agreement)", ticker=ticker)


