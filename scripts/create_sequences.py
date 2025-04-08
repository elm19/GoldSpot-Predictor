import numpy as np

def create_sequences(data, lookback):
        X, y = [], []
        for i in range(lookback, len(data)-6):
            X.append(data[i - lookback:i])
            y.append(data[i:i+6, 1])  # Predict the 'Close' price (index 1)
        return np.array(X), np.array(y)