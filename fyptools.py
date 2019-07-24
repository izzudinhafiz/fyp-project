import pandas as pd
import numpy as np
from alpha_vantage.timeseries import TimeSeries
import time
from datetime import datetime
from os import listdir
import random


def get_tickers(debug_level=0):
    # Return all available tickers
    if debug_level == 0:
        tickers = pd.read_csv("tickers.csv")
        tickers = sorted(tickers["Symbol"].tolist())

    # Return only AAPL ticker for debugging
    elif debug_level == 1:
        tickers = ["AAPL"]

    # Return 3 tickers for debugging
    elif debug_level == 2:
        tickers = ["AAPL", "AMZN", "MSFT"]

    # Return 1 random ticker for debugging
    elif debug_level == 3:
        tickers = pd.read_csv("tickers.csv")
        tickers = tickers["Symbol"]
        x = np.random.randint(0, len(tickers), size=1)
        tickers = [tickers.iloc[x[0]]]

    return tickers


def download_time_series(target="dataset", rate=4, time_type="daily", interval="5min"):
    tickers = get_tickers()

    ts = TimeSeries(key="7VFK1OI3AXXFQWAQ", output_format="pandas", retries=1)
    download_rate = rate

    # download Daily data for tickers
    # download Daily data for tickers
    if time_type == "daily":
        for i in range(len(tickers)):
            print("Downloading: " + str(tickers[i]))
            start = time.time()
            attempt = 0
            timeout = False
            success = False
            while not timeout:
                try:
                    data, meta_data = ts.get_daily_adjusted(tickers[i], outputsize="full")
                except Exception as exception_description:
                    if attempt < 3:
                        print("Error downloading, retrying soon")
                        print(type(exception_description))
                        print(exception_description.args)
                        retry_wait_time = 60 - (time.time() - start)
                        start = time.time()
                        if retry_wait_time > 0:
                            time.sleep(int(retry_wait_time))
                        attempt += 1
                    else:
                        timeout = True
                else:
                    timeout = True
                    success = True
                    data.to_csv(target + "/" + str(tickers[i]) + "_daily.csv")

            if success:
                # create comparison vector for identifying problem data lines
                o = data["1. open"].values
                h = data["2. high"].values
                l = data["3. low"].values
                c = data["4. close"].values

                # create empty mask to identify problem data lines
                mask = np.zeros(len(o))

                # find problem lines, such as OHLC data being the same
                for _ in range(len(o)):
                    if o[_] == c[_] and h[_] == c[_] and l[_] == c[_]:
                        mask[_] = 1

                # fix problem lines by fudging the data abit
                for mask_index in range(len(mask)):
                    if mask[mask_index] == 1:
                        data.loc[mask_index, "1. open"] = c[mask_index] * 1.01
                        data.loc[mask_index, "2. high"] = c[mask_index] * 1.03
                        data.loc[mask_index, "3. low"] = c[mask_index] * 0.98

                if int(mask.sum()) is not 0:
                    print("Repaired prob in " + str(tickers[i]))

                # adjust OHLC data to account for splits
                multiplier = data["5. adjusted close"] / data["4. close"]

                data["open"] = data["1. open"] * multiplier
                data["high"] = data["2. high"] * multiplier
                data["low"] = data["3. low"] * multiplier

                # rename column to standard OHLC
                data.rename(
                    columns={"4. close": "close_unadjusted", "5. adjusted close": "close", "6. volume": "volume"},
                    inplace=True)

                # remove unnecassary columns
                data.drop(columns={"8. split coefficient", "7. dividend amount", "1. open", "2. high", "3. low"},
                          inplace=True)

                # round data to 4 decimal places
                data = data.round({"open": 4, "high": 4, "low": 4, "close": 4})

                # save fixed_dataset seperate from raw dataset
                data.to_csv("fixed_dataset/" + str(tickers[i]) + "_daily_adjusted.csv")

            # wait certain amount of time to avoid API limit
            end = time.time()

            if end - start < int(60 / download_rate):
                wait_time = int(60 / download_rate) - (end - start)
            else:
                wait_time = 0

            print("Saved: " + str(tickers[i]) + " Took " + str(end - start) + " seconds")
            print("Completion: ", i + 1, "/", len(tickers))
            time.sleep(wait_time)

    elif time_type == "intraday" :
        for i in range(len(tickers)):
            try:
                print("Downloading: " + str(tickers[i]))

                start = time.time()
                data, meta_data = ts.get_intraday(tickers[i], interval=interval, outputsize="full")
                end = time.time()

                data.rename(columns={"1. open": "open", "2. high": "high", "3. low": "low", "4. close": "close",
                                     "5. volume": "volume"}, inplace=True)
                data.to_csv("intraday_data/" + str(tickers[i]) + "_" + str(interval) +
                            "_" + str(datetime.date.today()) + ".csv")

                print("Saved: " + str(tickers[i]) + " Took " + str(end - start) + " seconds")
                print("Completion: ", i + 1, "/", len(tickers))

                if end - start < int(60 / download_rate):
                    waittime = int(60 / download_rate) - (end - start)
                else:
                    waittime = 0
                time.sleep(waittime)

            except ValueError:
                print("API Limit Reached. Waiting 1 minute before trying again")
                time.sleep(60)

                print("Downloading: " + str(tickers[i]))
                start = time.time()
                try:
                    data, meta_data = ts.get_intraday(tickers[i], interval=interval, outputsize="full")
                    data.rename(columns={"1. open": "open", "2. high": "high", "3. low": "low", "4. close": "close",
                                         "5. volume": "volume"}, inplace=True)
                    end = time.time()
                    data.to_csv("intraday_data/" + str(tickers[i]) + "_" + str(interval) +
                                "_" + str(datetime.date.today()) + ".csv")
                    print("Saved: " + str(tickers[i]) + " Took " + str(end - start) + " seconds")
                    print("Completion: ", i + 1, "/", len(tickers))

                    if end - start < int(60 / download_rate):
                        waittime = int(60 / download_rate) - (end - start)
                    else:
                        waittime = 0
                    time.sleep(waittime)
                except ValueError:
                    print("Failed to download:", tickers[i])


def create_missing_list(target):
    tickers = get_tickers()

    files = [f for f in listdir(target)]

    tickers_downloaded = []

    got_two_csv = False

    # create a mask to know which CSV file is the one with tickers
    while not got_two_csv:
        index_1 = random.randint(0, len(files))
        index_2 = random.randint(0, len(files))
        csv1 = files[index_1]
        csv2 = files[index_2]

        # check if we grabbed csv files
        if csv1[-3:] == "csv" and csv2[-3:] == "csv":
            is_csv = True
        else:
            is_csv = False

        # get the ticker of the first CSV
        counter = 0
        for a in csv1:
            if a is not "_":
                counter += 1
            elif a is "_":
                csv1 = csv1[:counter]
                break
        mask_1 = files[index_1][counter:]

        # get the ticker of the second CSV
        counter = 0
        for a in csv2:
            if a is not "_":
                counter += 1
            elif a is "_":
                csv2 = csv2[:counter]
                break
        mask_2 = files[index_2][counter:]

        # done if we dont check the same file, is two csv and mask matches
        if (csv1 != csv2) and is_csv and (mask_1 == mask_2):
            got_two_csv = True
            mask = mask_1[:]

    for file in files:  # create a list of tickers in the directory
        if file[-len(mask):] == mask:  # check to see if the filename being compared matches the mask format
            tickers_downloaded.append(file[:-len(mask)])  # strip out the mask, keep the ticker name

    # create a list of missing tickers by comparing it to the master list
    missing_tickers = []
    for ticker in tickers:
        if ticker not in tickers_downloaded:
            missing_tickers.append(ticker)

    # save the list of missing tickers
    csv_path = target + "missing_tickers.csv"
    with open(csv_path, "w") as f:
        for ticker in missing_tickers:
            if ticker is not missing_tickers[-1]:
                f.write("{},".format(ticker))
            else:
                f.write(ticker)