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


# Create a Stratey
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

    def next(self):
        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return
        

        # Check if we are in the market
        if not self.position and  len(self) < len(self.predictions[0]):
            
            # Not yet ... we MIGHT BUY if ...
            atr_value = self.atr[0]
            if max(self.predictions[0][len(self) -10] - self.dataclose[0]) > self.p.atr_multiplier * atr_value:
                self.place_order("buy", atr_value)
            elif min(self.predictions[0][len(self) -10] - self.dataclose[0]) < -self.p.atr_multiplier * atr_value:
                self.place_order("sell", atr_value)
        
        # time.sleep(1)

    def place_order(self, order_type, atr_value):
        stop_loss_distance = atr_value * self.p.atr_multiplier

        capital = self.broker.getvalue()
        risk_amount = capital * self.p.risk_per_trade
        size = risk_amount / stop_loss_distance
        self.price = self.data.close[0]
        
        if order_type == "buy":
            self.stop_price = self.price - stop_loss_distance

            self.buy_bracket(
                price=self.price,
                size=size,
                stopprice=self.stop_price,
                limitprice=self.price + stop_loss_distance,
            )
        elif order_type=="sell":
            self.stop_price = self.price + stop_loss_distance

            self.sell_bracket(
                price=self.price,
                size=size,
                stopprice=self.stop_price,
                limitprice=self.price - stop_loss_distance,
            )
        self.trades.append({
            'entry_price': self.price,
            'stop_loss': self.stop_price,
            'order_type': order_type    
        })
        



if __name__ == '__main__':
    # Create a cerebro entity
    cerebro = bt.Cerebro()
    # Add a strategy
    cerebro.addstrategy(TestStrategy)
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    # cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')
    cerebro.addanalyzer(bt.analyzers.SQN, _name='sqn')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')

    # Datas are in a subfolder of the samples. Need to find where the script is
    # because it could have been called from anywhere
    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    datapath = os.path.join(modpath, '../data/processed-data/price-gold-cleaned.csv')

    # Create a Data Feed# Add a strategy
    data = bt.feeds.GenericCSVData(
        dataname=datapath,
        dtformat=('%Y-%m-%d'),
        datetime=0,
        time=-1,
        openinterest=-1,
        high=3,
        low=4,
        close=1,
        volume=5,
        open=2,
        # nullvalue=0.0
    )
    # Add the Data Feed to Cerebro
    cerebro.adddata(data)

    # Set our desired cash start
    cerebro.broker.setcash(10000.0)

    # Print out the starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Run over everything
    strats = cerebro.run()
    cerebro.plot()
    strat = strats[0]


    print("Total Trades:", strat.analyzers.trades.get_analysis()['total']['total'])
    print("Net Profit:", strat.analyzers.trades.get_analysis()['pnl']['net']['total'])
    print("Sharpe Ratio:", strat.analyzers.sharpe.get_analysis())
    print("Max Drawdown %:", strat.analyzers.drawdown.get_analysis()['max']['drawdown'])
    print("Max Drawdown Value:", strat.analyzers.drawdown.get_analysis()['max']['moneydown'])
    print("SQN:", strat.analyzers.sqn.get_analysis())
    print("Returns:", strat.analyzers.returns.get_analysis()['rtot'])
    
    # pyfoliozer = strat.analyzers.getbyname('pyfolio')
    # returns, positions, transactions, gross_lev = pyfoliozer.get_pf_items()


    # Print out the final result
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())



# //for further analysis later on we are going to use pyfolio
    # import pyfolio as pf
    # pf.create_full_tear_sheet(
    #     returns,
    #     positions=positions,
    #     transactions=transactions,
    #     gross_lev=gross_lev,
    #     live_start_date='2005-05-01',  # This date is sample specific
    #     round_trips=True)