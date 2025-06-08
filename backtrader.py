from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import backtrader as bt
import backtrader.analyzers as btanalyzers
import backtrader.strategies as btstrats

import pandas as pd 
import numpy as np
import pandas as pd
from keras.models import load_model


import os.path  # To manage paths
import sys
import time 
from datetime import datetime


import backtrader as bt
import backtrader.analyzers as btanalyzers
import backtrader.strategies as btstrats

df_raw = pd.read_csv('data/processed-data/g_2010_2023.csv', index_col="Date", parse_dates=["Date"])
print(df_raw.head())


import joblib
scaler = joblib.load('notebooks/new_approach_exp1/scaler.pkl')
from scripts.process import process
from collections import Counter
X, Y = process(df_raw, scaler, dev=False)

# 1) Load your saved model
model = load_model('notebooks/new_approach_exp1/regulized_model.keras')
proba   = model.predict(X)             
pred_ix = np.argmax(proba, axis=1)
class_map = {0: 'sell', 1: 'hold', 2: 'buy'}
pred_labels = [class_map[i] for i in pred_ix]


# lets count how many buy signals we got 
counts = Counter(pred_labels)
print("Counts:", counts)


# Create a Stratey
class TestStrategy(bt.Strategy):
    params = dict(
        atr_period=14,
        atr_multiplier=1.5,  # for stop-loss
        risk_per_trade = 0.01
    )

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close
        self.atr = bt.ind.ATR(self.data, period=self.p.atr_period)
        self.order = None
        
        


    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log('BUY EXECUTED, %.2f' % order.executed.price)
            elif order.issell():
                self.log('SELL EXECUTED, %.2f' % order.executed.price)

            self.bar_executed = len(self)

        elif order.status == order.Canceled:
            print("Order was canceled.")

        elif order.status == order.Margin:
            print("Order was rejected due to insufficient margin.")

        elif order.status == order.Rejected:
            print("Order was rejected by the broker.")

        # Write down: no pending order
        self.order = None

    def next(self):
        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return
        
        if not self.position and len(self) >= 34:
            if pred_labels[len(self)-34] == "buy":
                self.place_order("buy", self.atr)
            elif pred_labels[len(self)-34] == "sell":
                self.place_order("sell", self.atr)
            
        
        # time.sleep(1)

    def place_order(self, order_type, atr_value):
        stop_loss_distance = atr_value * self.p.atr_multiplier

        capital = self.broker.getvalue()
        risk_amount = capital * self.p.risk_per_trade
        size = risk_amount / stop_loss_distance
        self.price = self.data.close[0]
        
        if order_type == "buy":
            self.stop_price = self.price - stop_loss_distance
            # self.buy(size=size,  trailamount=stop_loss_distance)

            self.buy_bracket(
                price=self.price,
                size=size,
                # exectype=bt.Order.TrailingStop,
                # trailamount=stop_loss_distance,
                stopprice=self.stop_price,
                limitprice=self.price + stop_loss_distance,
            )
        elif order_type=="sell":
            self.stop_price = self.price + stop_loss_distance
            # self.sell(size=size,  trailamount=stop_loss_distance)
            self.sell_bracket(
                price=self.price,
                size=size,
                limitprice=self.price - stop_loss_distance,
                stopprice=self.stop_price
            )


