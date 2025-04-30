import numpy as np
from joblib import load
from keras.models import load_model

def create_sequences(data, lookback):
    X, y = [], []
    for i in range(lookback, len(data) - 6):
        X.append(data[i - lookback:i])
        y.append(data[i:i + 6])  # y sera une séquence de 6 valeurs (déjà normalisées)
    return np.array(X), np.array(y)

def inverse_transform_y(data, scaler_y):
    # Appliquer inverse_transform sur chaque colonne de la prédiction
    inv_data = np.zeros_like(data)
    for i in range(data.shape[1]):
        inv_data[:, i] = scaler_y.inverse_transform(data[:, i].reshape(-1, 1)).flatten()
    return inv_data

def predict_model(model_path, scalerX_path, scalerY_path, data, lookback_period=10):
    model = load_model(model_path)
    scalerX = load(scalerX_path)
    scalerY = load(scalerY_path)

    scaled_X = scalerX.transform(data)

    X, y = create_sequences(scaled_X, lookback_period)

    X_backtest = np.reshape(X, (X.shape[0], X.shape[1], X.shape[2]))

    predictions = model.predict(X_backtest)

    predictions_inv = inverse_transform_y(predictions, scalerY)
    y_inv = inverse_transform_y(y, scalerY)

    return predictions_inv, y_inv
