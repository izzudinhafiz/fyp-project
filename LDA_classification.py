import fyptools.label_data as label
import fyptools.helper_functions as helper
import fyptools.feature as feature
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis as LDA
from sklearn.preprocessing import StandardScaler

split_ratio = 0.2
start_date = "2000"
end_date = "2019"

ticker_df = helper.read_data("AAPL")
# ticker_df["decision"] = label.rto_label(ticker_df, 15)
# ticker_df["decision"] = label.cdnn_sezer(ticker_df)
ticker_df["decision"] = label.return_label(ticker_df)
ticker_df["decision"] = label.remove_lone_decision(ticker_df, cluster_ratio=0.2)
ticker_df["decision"] = label.cleanup_region_agreement(ticker_df)
ticker_df["macd"] = feature.macd(ticker_df)
ticker_df["bb_middle"], ticker_df["bb_upper"], ticker_df["bb_lower"] = feature.bollinger_band(ticker_df)
ticker_df["rsi"] = feature.rsi(ticker_df)
ticker_df.dropna(inplace=True)
ticker_df = ticker_df[start_date:end_date]

features = ["macd", "rsi", "bb_middle", "bb_lower", "bb_upper"]

val_length = int(len(ticker_df) * split_ratio)

training_data = ticker_df[:-val_length][features]
training_label = ticker_df[:-val_length]["decision"]
training_index = training_data.index.tolist()

validation_data = ticker_df[-val_length:][features]
validation_label = ticker_df[-val_length:]["decision"]
validation_index = validation_data.index.tolist()

lda = LDA()
scaler = StandardScaler()

scaler.fit(training_data.to_numpy())
tf_training_data = scaler.transform(training_data.to_numpy())
tf_validation_data = scaler.transform(validation_data.to_numpy())

lda.fit(tf_training_data, training_label.to_numpy())
predict_training = lda.transform(tf_training_data)
predict_validation = lda.transform(tf_validation_data)

cols = []
for _ in range(2):
    cols.append("lda{}".format(_+1))

predict_training = pd.DataFrame(predict_training, training_index, cols)
predict_validation = pd.DataFrame(predict_validation, validation_index, cols)
predict_training = pd.concat([predict_training, training_label], axis=1)
predict_validation = pd.concat([predict_validation, validation_label], axis=1)

labels = [1, -1, 0]
colors = ["g", "r", "k"]

# principal_data = predict_validation
principal_data = predict_training

for label, color in zip(labels, colors):
    index_to_keep = principal_data["decision"] == label
    plt.scatter(principal_data.loc[index_to_keep, "lda1"],
                principal_data.loc[index_to_keep, "lda2"],
                c=color, alpha=0.5, s=30)

plt.show()