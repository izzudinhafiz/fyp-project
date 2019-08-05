import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import math


def cdnn_sezer(data: pd.DataFrame, offsets: tuple = (4, 15), ticker: str = None, plot_hist: bool = False):
    """
    Labelling algorithm based on Sezer & Ozbayoglu (2019)
    where:
        ref_slope = (valueRefOffset - value) / refOffset
        current_slope = (valueCurOffset - value) / curOffset

    Paper list refOffset as 4 days into the future and curOffset as 15 days into the future

    Decision rules:
    Buy if current_slope > 3rd Quartile of ref_slope_sorted
    Sell if current slope < 1st Quartile of ref_slope_sorted

    :param data: Pandas DataFrame in OHLC format
    :param offsets: Window size in days (reference window, current window)
    :param ticker: Name of current ticker for histogram plot title
    :param plot_hist: If true, plot the histogram of reference slope
    :return: Pandas Series of decision
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


def return_label(data: pd.DataFrame, offset: int = 30, offset_type: str = "simple", required_return: float = None):
    """"
    Label decisions based on future return > required_return

    if offset_type == simple:
        compare (valueOffset - value) / value against required_return
    if offset_type == rolling_average:
        compare (rolling_average_value - value) / value against required_return

    :param data: Pandas DataFrame in OHLC format
    :param offset: Window size in days
    :param offset_type: Choice of "simple" or "rolling_average"
    :param required_return: Specify a hard limit return, if None, use 1st and 3rd quartile return
    :return: Pandas Series of decision
    """
    frame = data.copy()

    if offset_type == "simple":
        frame["future_return"] = (frame.close.shift(-offset) - frame.close) / frame.close
    elif offset_type == "rolling_average":
        frame["future_return"] = (frame.close.rolling(offset).mean().shift(-offset) - frame.close) / frame.close

    frame["decision"] = 0
    if required_return is not None:
        frame.loc[frame["future_return"] > required_return, "decision"] = 1
        frame.loc[frame["future_return"] < -required_return, "decision"] = -1
    else:
        ref_return = sorted(list(frame.future_return))
        buy_return = ref_return[int(0.75*len(ref_return))]
        sell_return = ref_return[int(0.25*len(ref_return))]
        frame.loc[frame["future_return"] > buy_return, "decision"] = 1
        frame.loc[frame["future_return"] < sell_return, "decision"] = -1
    return frame.decision


def rto_label(data: pd.DataFrame, offset: int = 30):
    """
    Regression Through Origin (RTO) Labelling

    Theory:
        RTO is calculated by minimizing square error between y_predict & y_actual
        Hence min(Square_Error) --> (y_predict - y_actual)**2
        y_predict is a linear function, y_predict = mx + c
        since we want to pass thru origin, c = 0, y_predict = mx
        Hence: min(Square_Error) --> (mx - y_actual)**2
        Since square_error is a quadratic function:
            Square_Error minimized when first derivative of Square_Error WRT x = 0
    Procedure:
        Translate points so starting point is on origin(0,0)
        Perform best fit regression running through origin
        Get slope, sort it, take 75% and 25% percentile slope as ref
        If slope > 75%, buy
        If slope < 25%, sell

    :param data: Pandas DataFrame containing index and AT LEAST close price
    :param offset: Number of days to lookahead
    :return: Pandas Series of "decision" column only
    """

    frame = data.copy()
    slope_arr = np.zeros(len(frame))
    close_arr = np.asarray(frame.close)

    # Go thru each point
    for i in range(len(frame.index)):
        if i < (len(frame) - offset):  # Check to see if enough data is available at end of frame given offset
            window_arr = close_arr[i:i+offset]  # Active window of array
            first_point = window_arr[0]
            window_arr = window_arr - first_point  # Translate points so starting point == Origin (0,0)
            x_data = np.asarray([x for x in range(len(window_arr))])  # X label, (0 to n)

            a = np.square(x_data).sum()  # Get Sum of Square of X
            b = (-2*x_data*window_arr).sum()  # Get sum of 2xy
            slope = -(b / (2*a))  # slope of a quadratic function for the error

            slope_arr[i] = slope / first_point  # normalize
    frame["slope"] = slope_arr

    # Determine threshold values for buy and sell
    ref_slope = sorted(list(frame["slope"]))
    buy_threshold = ref_slope[int(0.75*len(ref_slope))]
    sell_threshold = ref_slope[int(0.25*len(ref_slope))]

    # Make decision
    frame["decision"] = 0
    frame.loc[frame.slope > buy_threshold, "decision"] = 1
    frame.loc[frame.slope < sell_threshold, "decision"] = -1

    return frame.decision


def cleanup_neighbour_checking(data):
    pass


def cleanup_region_agreement(data: pd.DataFrame, thresh: float = 0.07):
    """
    Removes decisions that are not within the threshold range of its neighbours.
    The Point of Interest (POI) for buy is the minimum of the cluster, sell is maximum of cluster

    :param data: Pandas DataFrame in OHLC format, must already have "decision"
    :param thresh: Threshold value in decimal percentage, neighbours must be within threshold of min/max POI
    :return: Pandas Series with only the decision column
    """
    if "decision" not in data.columns:
        raise ValueError("Required column 'decision' is missing: Run one of the labelling function")

    def subsample_analysis(input_data: dict, condition: str, threshold: float):
        """
        Given a dictionary of cluster points, analyse the cluster to determine which points
        should be marked for removal

        :param input_data: Dictionary of {index: price}
        :param condition: String that is either "buy" or "sell"
        :param threshold: Threshold value
        :return: List of indexes of the points to be removed
        """
        if condition == "buy":
            min_value = math.inf
            for value in input_data.values():
                if value < min_value:
                    min_value = value

            remove_list = []
            threshold_value = min_value * (threshold + 1.0)
            for key, value in input_data.items():
                if value > threshold_value:
                    remove_list.append(key)

            return remove_list
        elif condition == "sell":
            max_value = -math.inf
            for value in input_data.values():
                if value > max_value:
                    max_value = value

            remove_list = []
            threshold_value = max_value * (1.0 - threshold)
            for key, value in input_data.items():
                if value < threshold_value:
                    remove_list.append(key)

            return remove_list

    # Copy input
    frame = data.copy()

    # Initialize state variables and convert corresponding data to Numpy Array for speeding up
    active_decision = {}
    decision_array = np.asarray(frame.decision)
    price = np.asarray(frame.close)
    state = "nothing"

    # State machine loop
    for i in range(len(frame)):
        current_action = decision_array[i]
        if state == "nothing" and current_action == 1:  # At the start, state is nothing, find the first B/S state
            state = "buy"
        elif state == "nothing" and current_action == -1:  # At the start, state is nothing, find the first B/S state
            state = "sell"
        elif state == "buy" and current_action == -1:  # Change of state from buy to sell
            state = "sell"  # Record change of state
            removal = subsample_analysis(active_decision, "buy", thresh)  # Pass the cluster for analysis
            active_decision.clear()  # Clear the dictionary for next use
            if removal is not None:  # Remove decisions that are marked for removal
                for item in removal:
                    decision_array[item] = 0
        elif state == "sell" and current_action == 1:  # Change of state from sell to buy
            state = "buy"  # Record change of state
            removal = subsample_analysis(active_decision, "sell", thresh)  # Pass the cluster for analysis
            active_decision.clear()  # Clear the dictionary for next use
            if removal is not None:  # Remove decisions that are marked for removal
                for item in removal:
                    decision_array[item] = 0

        # Include points that match state into dictionary of cluster
        if state == "buy" and current_action == 1:
            active_decision[i] = price[i]
        elif state == "sell" and current_action == -1:
            active_decision[i] = price[i]

    return frame.decision


def remove_lone_decision(data: pd.DataFrame, offset: int = 10, cluster_ratio: float = 0.1):
    """
    Removes any decision points not in a cluster within a certain window size.
    Clustering based on number of decision points set in cluster_ratio*offset

    :param data: Pandas DataFrame in OHLC format, must already have "decision"
    :param offset: Windows of days to look around, centered on value
    :param cluster_ratio: Ratio of offset such that a cluster must contain at least this amount of decision
    :return: Pandas Series with only the decision column
    """
    if "decision" not in data.columns:
        raise ValueError("Required column 'decision' is missing: Run one of the labelling function")

    # Threshold calculation
    threshold = round(offset * cluster_ratio)
    if threshold < 1:
        threshold = 1

    # Copy input DataFrame
    decision = data["decision"].copy()
    buy_decision = data["decision"].copy()
    sell_decision = data["decision"].copy()

    # Split buys and sells
    buy_decision.loc[buy_decision == -1] = 0
    sell_decision.loc[sell_decision == 1] = 0

    # Sum over the window
    buy_sum = buy_decision.rolling(offset, center=True).sum()
    sell_sum = sell_decision.rolling(offset, center=True).sum()

    # Keep only those sum with a corresponding decision
    sell_sum.loc[sell_decision != -1] = 0
    buy_sum.loc[buy_decision != 1] = 0

    # Remove decisions that are not in a cluster
    decision_remove = abs(sell_sum) + buy_sum
    decision.loc[decision_remove <= threshold] = 0

    return decision
