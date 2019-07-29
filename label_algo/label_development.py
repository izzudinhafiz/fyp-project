import pandas as pd
from fyptools import helper_functions as helper
import os
from fyptools import label_data as label


tickers = helper.get_tickers(1)

os.chdir("..")
main_df = pd.read_csv("fixed_dataset/" + tickers[0] + "_daily_adjusted.csv",
                      parse_dates=True, index_col="date")

main_df["decision"] = label.rto_label(main_df)
main_df["decision"] = label.cleanup_region_agreement(main_df)

helper.plot_price_data(main_df, days=500)