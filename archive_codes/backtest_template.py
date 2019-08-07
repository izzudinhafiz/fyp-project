from fyptools import label_data as label
from fyptools import helper_functions as hf
import pandas as pd
from fyptools import backtester

tickers = hf.get_tickers(2)
tickers = ["AAPL", "A"]
main_df = {}
for ticker in tickers:
    ticker_df = pd.read_csv("fixed_dataset/" + ticker + "_daily_adjusted.csv",
                            index_col="date", parse_dates=True)
    ticker_df["decision"] = label.rto_label(ticker_df, offset=15)
    ticker_df["decision"] = label.remove_lone_decision(ticker_df, cluster_ratio=0.2)
    ticker_df["decision"] = label.cleanup_region_agreement(ticker_df)
    main_df[ticker] = ticker_df

main_df = pd.concat(main_df, 1)
# main_df["AAPL", "decision2"] = label.rto_label(main_df["AAPL"], offset=15)
# print(main_df.index)

bt = backtester.Backtester(main_df, 100000, "1998", "2000")
decisions = main_df["AAPL", "decision"].loc["1998":"2000"].to_numpy()
decisions2 = main_df["A", "decision"].loc["1998":"2000"].to_numpy()
print(bt.tickers)
for i in range(len(bt.dates)-1):
    print(bt.has_data("A"))
    if decisions[i] == 1:
        tp = bt.get_price("AAPL") * 1.1
        sl = bt.get_price("AAPL") * 0.9
        bt.portfolio.open_position_value("AAPL", 1000, tp, sl)
    if decisions[i] == -1:
        tp = bt.get_price("AAPL") * 0.9
        sl = bt.get_price("AAPL") * 1.1
        bt.portfolio.open_position_value("AAPL", -1000, tp, sl)
    if decisions2[i] == 1:
        tp = bt.get_price("A") * 1.1
        sl = bt.get_price("A") * 0.9
        bt.portfolio.open_position_value("A", 1000, tp, sl)
    if decisions2[i] == -1:
        tp = bt.get_price("A") * 0.9
        sl = bt.get_price("A") * 1.1
        bt.portfolio.open_position_value("A", -1000, tp, sl)
    # if i == 5:
        # print(bt.portfolio.is_open("AAPL"))
        # print(bt.portfolio.is_open("MSFT"))
    bt.next_day()

print("End of Simulation")

bt.end_of_simulation()

print(bt.portfolio.cash)
summary = bt.history.get_summary()
short_summary = summary[["units", "open_value", "close_value", "true_profit", "open_commission", "close_commission", "close_type"]]
print(summary[["units", "open_value", "close_value", "true_profit", "open_commission", "close_commission", "close_type"]])
