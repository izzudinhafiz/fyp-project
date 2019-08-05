from fyptools import label_data as label
from fyptools import helper_functions as hf
import pandas as pd
from fyptools import backtester

tickers = hf.get_tickers(1)

main_df = pd.read_csv("fixed_dataset/" + tickers[0] + "_daily_adjusted.csv",
                      index_col="date", parse_dates=True)
main_df["decision"] = label.rto_label(main_df, offset=15)
main_df["decision"] = label.remove_lone_decision(main_df, cluster_ratio=0.2)
main_df["decision"] = label.cleanup_region_agreement(main_df)
decisions = main_df.decision.to_numpy()

bt = backtester.Backtester(main_df, 50000)

for i in range(10):
    print(bt.date)
    if i == 0:
        bt.buy_unit("AAPL", 1000)
    decision = decisions[i]
    print(bt.positions["AAPL"].current_value, bt.positions["AAPL"].unit)
    print(bt.positions["AAPL"].profit)
    bt.next_day()
