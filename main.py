from fyptools import label_data as label
import pandas as pd
import fyptools.helper_functions as helper
import fyptools.classifier as classifier
import fyptools.feature as feature
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

split_ratio = 0.2
start_date = "2000"
end_date = "2019"

ticker_df = helper.read_data("AAPL")
ticker_df["decision"] = label.rto_label(ticker_df, 15)
ticker_df["decision"] = label.remove_lone_decision(ticker_df, cluster_ratio=0.2)
ticker_df["decision"] = label.cleanup_region_agreement(ticker_df)
ticker_df["macd"] = feature.macd(ticker_df)
ticker_df["bb_middle"], ticker_df["bb_upper"], ticker_df["bb_lower"] = feature.bollinger_band(ticker_df)
ticker_df["rsi"] = feature.rsi(ticker_df)
ticker_df.dropna(inplace=True)

features = ["macd", "rsi", "bb_middle", "bb_lower", "bb_upper"]
val_length = int(len(ticker_df) * split_ratio)

training_data = ticker_df[:-val_length][features]
training_label = ticker_df[:-val_length]["decision"]
training_index = training_data.index.tolist()

validation_data = ticker_df[-val_length:][features]
validation_label = ticker_df[-val_length:]["decision"]
validation_index = validation_data.index.tolist()
