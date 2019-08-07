import fyptools.helper_functions as helper
import pandas as pd

tickers = helper.get_tickers(4, "fixed_dataset/")
failed_fix = []

for i, ticker in enumerate(tickers):
    ticker_df = helper.read_data(ticker)
    print("{}/{}".format(i, len(tickers)))

    if not isinstance(ticker_df.index, pd.DatetimeIndex):
        print("Fixing {}".format(ticker))
        to_remove = []

        for index in ticker_df.index:
            if len(index) != 10:
                to_remove.append(index)

        ticker_df.drop(to_remove, inplace=True)

        try:
            ticker_df.index = pd.to_datetime(ticker_df.index)
        except ValueError:
            print("Failed to fix {}".format(ticker))
            failed_fix.append(ticker)
        else:
            ticker_df.to_csv("fixed_dataset/{}_daily_adjusted.csv".format(ticker))

if len(failed_fix) != 0:
    with open("fixed_dataset/failed_fix.csv", "w") as f:
        for ticker in failed_fix:
            if ticker is not failed_fix[-1]:
                f.write("{},".format(ticker))
            else:
                f.write(ticker)