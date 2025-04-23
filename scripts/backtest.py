from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

# import datetime  # For datetime objects
import os.path  # To manage paths
import sys
import time 

# Import the backtrader platform
import backtrader as bt
import backtrader.analyzers as btanalyzers
import backtrader.strategies as btstrats


# Create a Stratey
class TestStrategy(bt.Strategy):
    params = dict(
        atr_period=14,
        atr_multiplier=1.5  # for stop-loss
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
        print(self.broker.getvalue())
        self.order = None

    def next(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.dataclose[0])
        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        # Check if we are in the market
        if not self.position:
            
            # Not yet ... we MIGHT BUY if ...
            if self.dataclose[0] < self.dataclose[-1]:
                    # current close less than previous close

                    if self.dataclose[-1] < self.dataclose[-2]:
                        # previous close less than the previous close

                        atr_value = self.atr[0]
                        risk_per_trade = 0.01  # 1% of portfolio
                        stop_loss_distance = atr_value * self.p.atr_multiplier
                        print('atr:', atr_value)

                        capital = self.broker.getvalue()
                        risk_amount = capital * risk_per_trade

                        # Position sizing based on how much we’re risking per share
                        size = risk_amount / stop_loss_distance
                        # Buy and store stop price
                        self.buy_price = self.data.close[0]
                        self.stop_price = self.buy_price - stop_loss_distance
                        self.log('Buy price: %.2f' % self.buy_price)
                        self.log('Stop price: %.2f' % self.stop_price)
                        self.log('Size: %.2f' % size)  
                        # self.buy_bracket(
                        #     price=self.buy_price,
                        #     size=size,
                        #     stopprice=self.stop_price
                        # )

                        self.buy()

                        # BUY, BUY, BUY!!! (with default parameters)
                        self.log('BUY CREATE, %.2f' % self.dataclose[0])


        else:

            # Already in the market ... we might sell
            if len(self) >= (self.bar_executed + 5):
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('SELL CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.sell()
        
        # time.sleep(1)



if __name__ == '__main__':
    # Create a cerebro entity
    cerebro = bt.Cerebro()

    # Add a strategy
    cerebro.addstrategy(TestStrategy)
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')
    cerebro.addanalyzer(bt.analyzers.SQN, _name='sqn')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')

    # Datas are in a subfolder of the samples. Need to find where the script is
    # because it could have been called from anywhere
    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    datapath = os.path.join(modpath, '../data/processed-data/price-gold-cleaned.csv')

    # Create a Data Feed
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
    cerebro.broker.setcash(100000.0)

    # Print out the starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Run over everything
    strats = cerebro.run()
    strat = strats[0]


    print("Total Trades:", strat.analyzers.trades.get_analysis()['total']['total'])
    print("Net Profit:", strat.analyzers.trades.get_analysis()['pnl']['net']['total'])
    print("Sharpe Ratio:", strat.analyzers.sharpe.get_analysis())
    print("Max Drawdown %:", strat.analyzers.drawdown.get_analysis()['max']['drawdown'])
    print("Max Drawdown Value:", strat.analyzers.drawdown.get_analysis()['max']['moneydown'])
    print("SQN:", strat.analyzers.sqn.get_analysis())
    print("Returns:", strat.analyzers.returns.get_analysis()['rtot'])
    
    pyfoliozer = strat.analyzers.getbyname('pyfolio')
    returns, positions, transactions, gross_lev = pyfoliozer.get_pf_items()


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