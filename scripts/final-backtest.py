from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

# import datetime  # For datetime objects
import os.path  # To manage paths
import sys
import time 
from datetime import datetime
# Import the backtrader platform
import backtrader as bt
import backtrader.analyzers as btanalyzers
import backtrader.strategies as btstrats

from . import predict_model


class TestStrategy(bt.Strategy):
    params = dict(
        atr_period=14,
        atr_multiplier=1.5,  # for stop-loss
        risk_per_trade = 0.01
    )
    predictions = predict_model.predict_model(
        'models/model1/lstm_model.keras',
        'models/model1/scaler.save',
        'data/processed-data/price-gold-cleaned.csv'
    )

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close
        self.atr = bt.ind.ATR(self.data, period=self.p.atr_period)
        self.trades = []
        # To keep track of pending orders
        self.order = None
        print(self.predictions)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
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
    def signal_generator(self, atr_value):

        if max(self.predictions[0][len(self) -10] - self.dataclose[0]) > self.p.atr_multiplier * atr_value:
            return "buy"
        elif min(self.predictions[0][len(self) -10] - self.dataclose[0]) < -self.p.atr_multiplier * atr_value:
            return "sell"
        else:
            return "hold"

    def next(self):
        print(self.predictions[0])
        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:

            return
        

        # Check if we are in the market
        if not self.position and  len(self) < len(self.predictions[0]):
            
            # Not yet ... we MIGHT BUY if ...
            atr_value = self.atr[0]
            print(self.predictions[0])
            # if self.signal_generator(atr_value) == "buy":
            #     # self.place_order("buy", atr_value)
            # elif self.signal_generator(atr_value) == "sell":
            #     self.place_order("sell", atr_value)
        
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
        
