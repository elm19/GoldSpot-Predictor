import numpy as np 
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

from joblib import load
from keras.models import load_model

def create_sequences(data, lookback):
        X, y = [], []
        for i in range(lookback, len(data)-6):
            X.append(data[i - lookback:i])
            y.append(data[i:i+6, 1])  # Predict the 'Close' price (index 1)
        return np.array(X), np.array(y)

def inverse_transform(data, scaler):
    # Inverse transform the predictions
    predicted_inv = np.zeros((data.shape[0], data.shape[1]))
    for i in range(data.shape[1]):
        dummy_predictions = np.zeros((len(data), 5))
        dummy_predictions[:, 1] = data[:, i]
        predicted_inv[:, i] = scaler.inverse_transform(dummy_predictions)[:, 1]


    return predicted_inv

def predict_model(model_path, scaler_path , data_path, lookback_period=10):
    model = load_model(model_path)
    scaler = load(scaler_path)
    data = pd.read_csv(data_path, index_col='datetime',  parse_dates=True)
    data = data[['Open', 'Close', 'High', 'Low', 'Vol.']]
    scaled_data = scaler.transform(data)
    X, y = create_sequences(scaled_data, lookback_period)
    X_backtest = np.reshape(X, (X.shape[0], X.shape[1], X.shape[2]))

    predictions = model.predict(X_backtest)
    # Inverse transform the predictions
    predictions = inverse_transform(predictions, scaler)
    
    reely = inverse_transform(y, scaler)
    return predictions, reely
