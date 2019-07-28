import pandas as pd
from fyptools import helper_functions as helper
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

tickers = helper.get_tickers(1)

main_df = pd.read_csv("fixed_dataset/" + tickers[0] + "_daily_adjusted.csv",
                      parse_dates=True, index_col="date")
main_df["slope"] = 0

for i, index in enumerate(main_df.index):
    window_df = np.asarray(main_df.loc[main_df.index[i:i+30], "close"])
    window_df = window_df - window_df[0]
    x_data = np.asarray([x for x in range(len(window_df))])

    a = np.square(x_data).sum()
    b = (-2*x_data*window_df).sum()
    slope = -(b / (2*a))

    main_df.loc[index, "slope"] = slope

print(main_df)