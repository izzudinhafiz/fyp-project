from fyptools import helper_functions as hf
import pandas as pd
import matplotlib.pyplot as plt

def cdnn_sezer(data, ticker=None, plot_hist=False, offsets=[4,15]):
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

    main_df = data.copy()

    # days to offset
    ref_offset = offsets[0]
    current_offset = offsets[1]

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

    if plot_hist:
        # plot histogram of ref_slope and the location of 3rd & 1st quartile
        plt.hist(ref_slope, bins=200)
        plt.axvline(buy_ref_slope, c="g")
        plt.axvline(sell_ref_slope, c="r")
        if ticker is not None:
            plt.title(ticker)
        plt.show()

    return main_df.decision


def return_label(data, offset=30, offset_type="simple", required_return=0.03):
    '''
    Label decisions based on future return > required_return

    if offset_type == simple:
        compare (valueOffset - value) / value against required_return
    if offset_type == rolling_average:
        compare (rolling_average_value - value) / value against required_return
    '''
    frame = data.copy()

    if offset_type == "simple":
        frame["future_return"] = (frame.close.shift(-offset) - frame.close) / frame.close
    elif offset_type == "rolling_average":
        frame["future_return"] = (frame.close.rolling(offset).mean().shift(-offset) - frame.close) / frame.close

    frame["decision"] = 0
    frame.loc[frame["future_return"] > required_return, "decision"] = 1
    frame.loc[frame["future_return"] < -required_return, "decision"] = -1

    return frame.decision

