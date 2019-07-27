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
    x_data = [x for x in range(len(window_df))]

    m, c, p, r, std_err = stats.linregress(x_data, window_df)
    best_line = [x * m + c for x in range(len(x_data))]
    mid_point = 0
    if len(best_line) % 2 == 0:
        # 0,1,2,3,4,5,6,7,8,9
        mid_index = (len(x_data) - 1) / 2
        mid_point = (best_line[int(mid_index - 0.5)] + best_line[int(mid_index + 0.5)]) / 2
        plt.plot(mid_index, mid_point, "rx")
    else:
        # 0,1,2,3,4,5,6,7,8
        mid_index = (len(best_line) - 1) / 2
        mid_point = best_line[int(mid_index)]
        plt.plot(mid_index, mid_point, "rx")

    slope = (mid_point - window_df[0]) / mid_index

    main_df.loc[index, "slope"] = slope

print(main_df)