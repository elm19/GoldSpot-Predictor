import pandas_ta as ta
from keras.utils import to_categorical
import pandas as pd
import numpy as np

def treat(df):
    df.drop(columns=['Change %'], inplace=True)

    # Remove commas and convert to float for the 'Close' column
    df['Price'] = df['Price'].replace(",", "", regex=True).astype(float)
    df['Open'] = df['Open'].replace(",", "", regex=True).astype(float)
    df['High'] = df['High'].replace(",", "", regex=True).astype(float)
    df['Low'] = df['Low'].replace(",", "", regex=True).astype(float)
    df['Vol.'] = df['Vol.'].replace("K", "e3", regex=True).astype(float)


    df.rename(columns={'Price': 'close'}, inplace=True)
    df.rename(columns={'Open': 'open'}, inplace=True)
    df.rename(columns={'High': 'high'}, inplace=True)
    df.rename(columns={'Low': 'low'}, inplace=True)
    df.rename(columns={'Vol.': 'volume'}, inplace=True)

    return df


def indicators(df):
    # Add several technical indicators
    df['SMA_20'] = ta.sma(df['close'], length=20)  # 50-day Simple Moving Average
    df['RSI'] = ta.rsi(df['close'], length=14)  # Relative Strength Index (14-day)
    # df['MACD'] = ta.macd(df['close'])['MACD']  # MACD (Moving Average Convergence Divergence)
    df['ATR'] = ta.atr(df['high'], df['low'], df['close'], length=14)  # Average True Range
    df.ta.macd(append=True)

    df.dropna(inplace=True)
    return df



def add_target(df, lookahead=5):
    """
    Add a 'target' column to the DataFrame.
    Look ahead up to number(lookahead) days; as soon as:
      - Close ≥ current_close + 1.5*ATR  ⇒ target = 1
      - Close ≤ current_close − 1.5*ATR  ⇒ target = -1
    If neither threshold is hit within 7 days ⇒ target = 0
    """
    df = df.copy()
    closes = df['close'].values
    atrs   = df['ATR'].values
    n      = len(df)
    targets = np.zeros(n, dtype=int)

    for i in range(n):
        up_thresh   = closes[i] + 1.5 * atrs[i]
        down_thresh = closes[i] - 1.5 * atrs[i]
        # look ahead day by day
        for future_close in closes[i+1 : i+1+lookahead]:
            if future_close >= up_thresh:
                targets[i] = 1
                break
            elif future_close <= down_thresh:
                targets[i] = -1
                break
        # if loop exits normally, targets[i] stays 0

    df['target'] = targets
    return df


def standardize(df, scaler=None):
    df = df.copy()
    features = df.drop(columns=['target']) if 'target' in df.columns else df
    
    scaled = scaler.transform(features)
    scaled_df = pd.DataFrame(scaled, columns=features.columns, index=df.index)
    if 'target' in df.columns:
        scaled_df['target'] = df['target'].values

    return scaled_df


def sequence(df, seq_len=20):
    target = df['target']
    # Encode target as 0, 1, 2
    target_map = {-1: 0, 0: 1, 1: 2}
    y = target.map(target_map).values


    # Create sequences
    X, Y = [], []
    for i in range(seq_len, len(df)):
        X.append(df[i-seq_len:i])
        Y.append(y[i])

    X = np.array(X)
    Y = to_categorical(Y, num_classes=3)

    return X, Y


def process(df_raw, scaler, dev = True, ind=True):
    df = df_raw.copy()
    if dev: 
        df = treat(df)
        df = df_raw.iloc[::-1]
    if ind:
        
        df = indicators(df)
    df = add_target(df, lookahead=7)
    
    df = standardize(df, scaler=scaler)
    X, Y = sequence(df)
    return X, Y




# if __name__ == '__main__':
    

#     # Read the CSV file
#     df_raw = pd.read_csv('data/raw-data/2025.csv', index_col="Date", parse_dates=["Date"])

#     # Process the DataFrame
#     X,y = process(df_raw)

#     print(X, y)
    