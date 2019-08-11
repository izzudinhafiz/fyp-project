import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler


class StockData:
    batch_size = 50

    def __init__(self, data, ticker, start, end, split_ratio=0.2):
        self.ticker = ticker
        self.data = data[start:end].copy()
        self.dates = self.data.index.tolist()
        self.original_features = self.data.columns.tolist()
        self.original_features.remove("decision")
        self.features = self.original_features
        training_length = int(len(self.data) * (1 - split_ratio))
        self.training_data = self.data[:training_length]
        self.validation_data = self.data[training_length:]
        self.training_label = self.training_data["decision"].copy()
        self.validation_label = self.validation_data["decision"].copy()
        self.training_features = self.data[:training_length].drop(columns="decision")
        self.validation_features = self.data[training_length:].drop(columns="decision")
        self.counter = 0

    def set_features(self, features: list):
        assert type(features) == list, "Features should be list, given {} instead".format(type(features))
        self.features = features
        self.training_features = self.training_data[features]
        self.validation_features = self.training_data[features]


def pca_classifier(dataframe, ticker, start, end, split_ratio=0.2, n_comp=None):
    data = StockData(dataframe, ticker, start, end, split_ratio)
    pca = PCA(n_components=n_comp)
    scaler = StandardScaler()
    index = data.training_data.index

    data.training_features = scaler.fit_transform(data.training_features)
    pca.fit(data.training_features.to_numpy())
