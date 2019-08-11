from fyptools import label_data as label
import pandas as pd
from fyptools import backtester
import fyptools.helper_functions as helper

tickers = ["AAPL", "A"]
main_df = {}
for ticker in tickers:
    ticker_df = helper.read_data(ticker)
    ticker_df["decision"] = label.rto_label(ticker_df, offset=15)
    ticker_df["decision"] = label.remove_lone_decision(ticker_df, cluster_ratio=0.2)
    ticker_df["decision"] = label.cleanup_region_agreement(ticker_df)
    main_df[ticker] = ticker_df

main_df = pd.concat(main_df, 1)

bt = backtester.Backtester(main_df, 100_000, "2003", "2010")
decisions = main_df["AAPL", "decision"].loc["2003":"2019"].to_numpy()

for i in range(len(bt.dates)-1):
    if bt.portfolio.is_open("AAPL"):
        if bt.portfolio.open_type("AAPL") == "long":
            if decisions[i] == -1:
                bt.portfolio.positions[bt.portfolio.get_id("AAPL")].manually_close()
        elif bt.portfolio.open_type("AAPL") == "short":
            if decisions[i] == 1:
                bt.portfolio.positions[bt.portfolio.get_id("AAPL")].manually_close()
    elif decisions[i] == 1:
        bt.portfolio.open_position_value("AAPL", bt.portfolio.cash)
    elif decisions[i] == -1:
        bt.portfolio.open_position_value("AAPL", -bt.portfolio.cash)

    bt.next_day()

bt.end_of_simulation()
print(bt.history.daily_history)
summary = bt.history.get_summary()
profit = sum(summary["true_profit"])
annualized_return = (bt.portfolio.cash/100_000)**(1/13) - 1
print(profit + 100_000, bt.portfolio.cash, bt.portfolio.equity)
print("End of Simulation")
print("Annualized Return: {:.2f}%".format(bt.portfolio.annualized_return*100))
bt.history.plot_history()
