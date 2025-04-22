import backtrader as bt
import pandas as pd



class MyStrategy(bt.Strategy):
    def __init__(self):
        self.sma = bt.indicators.SimpleMovingAverage(self.data.close, period=20)

    def next(self):
        if self.data.close[0] > self.sma[0]:
            if not self.position:
                self.buy()
        elif self.data.close[0] < self.sma[0]:
            if self.position:
                self.sell()

# Load data and run the backtest

data = pd.read_csv('data/processed-data/price-gold.csv')

cerebro = bt.Cerebro()
cerebro.addstrategy(MyStrategy)
cerebro.adddata(data)
cerebro.run()
cerebro.plot()
