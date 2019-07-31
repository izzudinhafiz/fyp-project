from fyptools import label_data as label
from fyptools import helper_functions as hf
import pandas as pd
import time

tickers = hf.get_tickers(1)

for ticker in tickers:
    main_df = pd.read_csv("fixed_dataset/" + ticker + "_daily_adjusted.csv",
                          index_col="date", parse_dates=True)

    # main_df["decision"] = label.return_label(main_df, offset=15, offset_type="simple", required_return=0.03)
    # main_df["decision"] = label.rto_label(main_df, offset=15)
    main_df["decision"] = label.cdnn_sezer(main_df)
    # main_df["decision"] = label.remove_lone_decision(main_df, offset=15, cluster_ratio=0.2)
    # main_df["decision"] = label.cleanup_region_agreement(main_df, 0.07)
    plot_title = "CDNN Sezer[(4,15)]"
    file_name = "CDNN Sezer Label"
    hf.plot_price_data(main_df, days=500, title=plot_title, ticker=ticker, save_plot=True, filename=file_name)

