from fyptools import label_data as label
import pandas as pd
import fyptools.helper_functions as helper
import fyptools.classifier as classifier
import fyptools.feature as feature
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

ticker_df = helper.read_data("AAPL")
ticker_df["decision"] = label.rto_label(ticker_df, 15)
ticker_df["decision"] = label.remove_lone_decision(ticker_df, cluster_ratio=0.2)
ticker_df["decision"] = label.cleanup_region_agreement(ticker_df)
ticker_df["macd"] = feature.macd(ticker_df)
ticker_df["bb_middle"], ticker_df["bb_upper"], ticker_df["bb_lower"] = feature.bollinger_band(ticker_df)
ticker_df["rsi"] = feature.rsi(ticker_df)
ticker_df.dropna(inplace=True)

val_length = 1000

features = ["macd", "rsi", "bb_middle", "bb_lower", "bb_upper"]
training_data = ticker_df[:-val_length][features]
training_label = ticker_df[:-val_length]["decision"]
training_index = training_data.index.tolist()
training_features = training_data.columns.tolist()
validation_label = ticker_df[-val_length:]["decision"]
validation_data = ticker_df[-val_length:][features]
validation_index = validation_data.index.tolist()

pca = PCA()
scaler = StandardScaler()

scaler.fit(training_data.to_numpy())
transformed_data = scaler.transform(training_data.to_numpy())

pca.fit(transformed_data)
training_components = pca.transform(transformed_data)

validation_data = scaler.transform(validation_data.to_numpy())
prediction_components = pca.transform(validation_data)


cols = []
for _ in range(len(features)):
    cols.append("pca{}".format(_+1))

principal_data = pd.DataFrame(prediction_components, index=validation_index, columns=cols)
principal_data = pd.concat([principal_data, validation_label], axis=1)

principal_data = pd.DataFrame(training_components, index=training_index, columns=cols)
principal_data = pd.concat([principal_data, training_label], axis=1)

labels = [1, -1, 0]
colors = ["g", "r", "k"]

# for label, color in zip(labels, colors):
#     index_to_keep = principal_data["decision"] == label
#     plt.scatter(principal_data.loc[index_to_keep, "pca3"],
#                 principal_data.loc[index_to_keep, "pca2"],
#                 c=color, alpha=0.8, s=10)
#
# plt.show()
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
for label, color in zip(labels, colors):
    index_to_keep = principal_data["decision"] == label
    ax.scatter(principal_data.loc[index_to_keep, "pca1"],
               principal_data.loc[index_to_keep, "pca2"],
               principal_data.loc[index_to_keep, "pca3"],
               c = color)

ax.set_xlabel("pca1")
ax.set_ylabel("pca2")
ax.set_zlabel("pca3")

plt.show()