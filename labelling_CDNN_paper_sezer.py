import fyptools as ft
import pandas as pd
import matplotlib.pyplot as plt

"""
Labelling algorithm based on Sezer & Ozbayoglu (2019)
where: 
    ref_slope = (valueRefOffset - value) / refOffset
    current_slope = (valueCurOffset - value) / curOffset
    
Paper list refOffset as 4 days into the future and curOffset as 15 days into the future

Decision rules:
Buy if current_slope > 3rd Quartile of ref_slope_sorted
Sell if current slope < 1st Quartile of ref_slope_sorted
"""

tickers = ft.get_tickers(1)

# days to offset
ref_offset = 4
current_offset = 15

for ticker in tickers:
    main_df = pd.read_csv("fixed_dataset/" + ticker + "_daily_adjusted.csv",
                          index_col="date", parse_dates=True)

    # create offset frame to calculate ref_slope and current_slope
    ref_slope_offset = main_df.close.copy().shift(-ref_offset)
    current_slope_offset = main_df.close.copy().shift(-current_offset)

    # calculate slopes
    main_df["ref_slope"] = (ref_slope_offset - main_df.close)/ref_offset
    main_df["current_slope"] = (current_slope_offset - main_df.close)/current_offset

    # cleanup
    main_df = main_df.round(decimals={"ref_slope" : 5, "current_slope" : 5})

    # sort ref_slope and get 3rd & 1st quartile
    ref_slope = sorted(main_df.ref_slope.dropna().tolist())
    buy_ref_slope = ref_slope[int(0.75*len(ref_slope))]
    sell_ref_slope = ref_slope[int(0.25*len(ref_slope))]

    # create decision column and populate value
    main_df["decision"] = 0
    main_df.loc[main_df.current_slope > buy_ref_slope, "decision"] = 1
    main_df.loc[main_df.current_slope < sell_ref_slope, "decision"] = -1

    # plot histogram of ref_slope and the location of 3rd & 1st quartile
    plt.hist(ref_slope, bins=200)
    plt.title(ticker)
    plt.axvline(buy_ref_slope, c="g")
    plt.axvline(sell_ref_slope, c="r")
    plt.show()

    # plot price and overlay decision
    ft.plot_price_data(main_df, "close", days=100)
