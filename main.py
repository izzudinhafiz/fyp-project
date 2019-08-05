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
decisions = main_df.loc["2000":"2018", "decision"].to_numpy()

bt = backtester.Backtester(main_df, 100000, "2000", "2018")

for i in range(len(bt.dates)-1):
    if decisions[i] == 1:
        tp = bt.get_price() * 1.1
        sl = bt.get_price() * 0.9
        bt.portfolio.open_position_unit("AAPL", 10, tp, sl)
    if decisions[i] == -1:
        tp = bt.get_price() * 0.9
        sl = bt.get_price() * 1.1
        bt.portfolio.open_position_unit("AAPL", -10, tp, sl)
    if i == 5:
        print(bt.portfolio.is_open("AAPL"))
        print(bt.portfolio.is_open("MSFT"))
    bt.next_day()


bt.end_of_simulation()

print(bt.portfolio.cash)
summary = bt.history.get_summary()
short_summary = summary[["units", "open_value", "close_value", "true_profit", "open_commission", "close_commission", "close_type"]]
# hf.plot_price_data(main_df, start_date="2010", end_date="2011")
print(summary[["units", "open_value", "close_value", "true_profit", "open_commission", "close_commission", "close_type"]])
# print(bt.history.get_position_summary_by_id(0))
# print(bt.history.get_position_summary_by_ticker("AAPL"))
