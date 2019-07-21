import pandas as pd
import numpy as np
from alpha_vantage.timeseries import TimeSeries
import time
from datetime import datetime

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

    #download Daily data for tickers
    if time_type == "daily":
        for i in range(len(tickers)):
            #try once
            try:
                print("Downloading: " + str(tickers[i]))
                start = time.time()
                data, meta_data = ts.get_daily_adjusted(tickers[i], outputsize="full")
                end = time.time()
                data.to_csv(target + "/" + str(tickers[i]) + "_daily.csv")
                print("Saved: " + str(tickers[i]) + " Took " + str(end - start) + " seconds")
                print("Completion: ", i + 1, "/", len(tickers))

                #wait certain amount of time to avoid API limit
                if end - start < int(60 / download_rate):
                    waittime = int(60 / download_rate) - (end - start)
                else:
                    waittime = 0
                time.sleep(waittime)

            #if failed due to API Limit, wait and try again
            except ValueError:
                print("API Limit Reached. Waiting 1 minute before trying again")
                time.sleep(60)
                print("Downloading: " + str(tickers[i]))
                start = time.time()
                data, meta_data = ts.get_daily_adjusted(tickers[i], outputsize="full")
                end = time.time()
                data.to_csv(target + "/"+ str(tickers[i]) + "_daily.csv")
                print("Saved: " + str(tickers[i]) + " Took " + str(round(end - start, 1)) + " seconds")
                print("Completion: ", i + 1, "/", len(tickers))
                if end - start < int(60 / download_rate):
                    waittime = int(60 / download_rate) - (end - start)
                else:
                    waittime = 0

                time.sleep(waittime)

            #create comparison vector for identifying problem data lines
            o = data["1. open"].values
            h = data["2. high"].values
            l = data["3. low"].values
            c = data["4. close"].values

            #create empty mask to identify problem data lines
            mask = np.zeros(len(o))

            # find problem lines, such as OHLC data being the same
            for _ in range(len(o)):
                if o[_] == c[_] and h[_] == c[_] and l[_] == c[_]:
                    mask[_] = 1

            #fix problem lines by fudging the data abit
            for mask_index in range(len(mask)):
                if mask[mask_index] == 1:
                    data.loc[mask_index, "1. open"] = c[i] * 1.01
                    data.loc[mask_index, "2. high"] = c[i] * 1.03
                    data.loc[mask_index, "3. low"] = c[i] * 0.98
                    print("Repaired prob in " + str(tickers[i]) + " at line " + str(mask_index))

            #adjust OHLC data to account for splits
            multiplier = data["5. adjusted close"] / data["4. close"]

            data["open"] = data["1. open"] * multiplier
            data["high"] = data["2. high"] * multiplier
            data["low"] = data["3. low"] * multiplier

            #rename column to standard OHLC
            data.rename(columns={"4. close": "close_unadjusted", "5. adjusted close": "close", "6. volume": "volume"},
                        inplace=True)

            #remove unnecassary columns
            data.drop(columns={"8. split coefficient", "7. dividend amount", "1. open", "2. high", "3. low"}, inplace=True)

            #round data to 4 decimal places
            data = data.round({"open": 4, "high": 4, "low": 4, "close": 4})

            #save fixed_dataset seperate from raw dataset
            data.to_csv("fixed_dataset/" + str(tickers[i]) + "_daily_adjusted.csv")

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
