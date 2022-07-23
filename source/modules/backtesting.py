# %% 
# Python modules. 
import csv 
import backtrader as bt 
from backtrader.feeds import PandasData 



# %%
def format_time(t):
    m_, s = divmod(t, 60)
    h , m = divmod(m_, 60)
    return f"{h:>02.0f}:{m:>02.0f}:{s:>02.0f}"



# %%
class FixedCommisionScheme(bt.CommInfoBase):
    """
    Define the commission scheme. 
	— https://github.com/mementum/backtrader/blob/e2674b1690f6366e08646d8cfd44af7bb71b3970/backtrader/comminfo.py#L30
    """
    
    params = (
        ("commission", .02),
        ("stocklike", True),
        ("commtype", bt.CommInfoBase.COMM_FIXED),
    )

    def _getcommission(self, size, price, pseudoexec):
        return abs(size) * self.p.commission



# %%
class SignalData(PandasData):
	"""
	Define pandas DataFrame structure. 
	— https://github.com/mementum/backtrader/blob/e2674b1690f6366e08646d8cfd44af7bb71b3970/backtrader/feeds/pandafeed.py#L107
	"""
    
	ohlvc = ["open", "high", "low", "close", "volume"]
	fcols = ohlvc + ["signal"]

	# All parameters related to lines must have numeric values as indices into the tuples. 
	lines = tuple(fcols)
 
	# Define parameters. 
	# — (None)   : Col is the "index" in the Pandas Dataframe. 
	# — (-1)     : No index, autodetect columns. 
	# — (>= 0)   : Numeric index for the colum identifier. 
	# — (string) : Column name (as index) in the pandas dataframe. 
	params = {c: -1 for c in fcols}
	params.update({"datetime": None})
	params = tuple(params.items()) 



# %%
class ConfigStrategy(bt.Strategy):
    """
    Define the investment or trading strategy. 
        — https://github.com/mementum/backtrader/blob/e2674b1690f6366e08646d8cfd44af7bb71b3970/backtrader/strategy.py#L107
    """

    def log(self, txt, dt=None):
        """Logger for the strategy."""

        dt = dt or self.datas[0].datetime.datetime() 
        with open(self.p.log_file, mode="a") as f:
            log_writer = csv.writer(f)
            log_writer.writerow([dt.isoformat()] + txt.split(","))

    def notify_order(self, order):
        """Notify the completed orders."""

        if order.status in [order.Submitted, order.Accepted]:
            return

        # Check if an order has been completed broker could 
        # reject order if not enough cash. 
        if self.p.verbose:

            if order.status in [order.Completed]:
                p = order.executed.price
                if order.isbuy():
                    self.log(f"{order.data._name}, BUY executed,{p:.2f}")
                elif order.issell():
                    self.log(f"{order.data._name}, SELL executed,{p:.2f}")

            elif order.status in [order.Canceled, order.Margin, order.Rejected]:
                self.log(f"{order.data._name}, Order Canceled / Margin / Rejected")

    def prenext(self):
        """
        (bt) calls (prenext) instead of next unless all datafeeds have 
        current values so call next to avoid duplicating logic. 
        """ 
        self.next()



# %%
class MLStrategy(ConfigStrategy):
    """
    Define the investment or trading strategy. 
        — https://github.com/mementum/backtrader/blob/e2674b1690f6366e08646d8cfd44af7bb71b3970/backtrader/strategy.py#L107
    """

    params = (
        ("n_positions", 10),
        ("min_positions", 5),
        ("verbose", False),
        ("log_file", "backtest.csv"),
    )

    def next(self):
        """Execute the strategy. Take or close the position at each iteration."""

        today = self.datas[0].datetime.date() 

        # # Only trade on Mondays. 
        # if today.weekday() not in [0, 3]: 
        #     return 

        up, down = {}, {}
        missing = not_missing = 0

        for data in self.datas:
            # Assign the predicted value to the (predicted) column for each date. 
            # Key = ticker name. Value = predicted forward return. 
            if data.datetime.date() == today:
                if data.predicted[0] > 0:
                    up[data._name] = data.predicted[0]
                elif data.predicted[0] < 0:
                    down[data._name] = data.predicted[0]

        # Sort dictionaries ascending/descending by valu. Returns list of tuples. 
        # Get the top N tickers for the highest return (long) and lowest return (short). 
        ls_short = sorted(down, key=down.get)[:self.p.n_positions]
        ls_longs = sorted(up, key=up.get, reverse=True)[:self.p.n_positions]
        n_short, n_longs = len(ls_short), len(ls_longs)
        
        # Only take positions if at least min N longs and short. 
        if n_short < self.p.min_positions or n_longs < self.p.min_positions:
            ls_longs, ls_short = [], []

        # Close the position. 0 here will set the target percentage to 0 when multiplied. 
        positions = [d._name for d, pos in self.getpositions().items() if pos]
        for ticker in positions:
            if ticker not in ls_longs + ls_short:
                self.order_target_percent(data=ticker, target=0)
                self.log(f"{ticker}, CLOSING ORDER CREATED")

        # Set target percentage of porfolio to invest into. X % of the porfolio will be 
        # divided equally among the N position or short / long. Short "borrows cash" so 
        # you have another X % of "borrowed money" for short here. 
        short_target = -1 / max(self.p.n_positions, n_short)
        longs_target = 1 / max(self.p.n_positions, n_longs)

        # Take or exit the position. If (data:=str) it will automatically get the ticker data. 
        # The target percent here indicates the percentage of porfolio to invest into. 
        for ticker in ls_short:
            self.order_target_percent(data=ticker, target=short_target)
            self.log("{ticker}, SHORT ORDER CREATED")
        for ticker in ls_longs:
            self.order_target_percent(data=ticker, target=longs_target)
            self.log("{ticker}, LONG ORDER CREATED")



# %% 
class RuleBasedStrategy(ConfigStrategy):
    """
    Define the investment or trading strategy. 
        — https://github.com/mementum/backtrader/blob/e2674b1690f6366e08646d8cfd44af7bb71b3970/backtrader/strategy.py#L107
    """

    params = (
        ("n_positions", 10),
        ("min_positions", 5),
        ("verbose", False),
        ("log_file", "backtest.csv"),
    )

    def next(self):
        """Execute the strategy. Take or close the position at each iteration."""

        today = self.datas[0].datetime.date()

        ls_short, ls_longs = set(), set()

        for data in self.datas:
            # If the signal is detected, append to the list for ordering later. 
            if data.datetime.date() == today:
                if data.signal[0] == 1:
                    ls_longs.add(data._name)
                elif data.signal[0] == -1:
                    ls_short.add(data._name)
                    
        n_short, n_longs = len(ls_short), len(ls_longs)
        
        # Only take positions if at least min N longs and short. 
        if n_short < self.p.min_positions and n_longs < self.p.min_positions:
            ls_short, ls_longs = set(), set()

        # Close the position. 0 here will set the target percentage to 0 when multiplied. 
        positions = [d._name for d, pos in self.getpositions().items() if pos]
        for ticker in positions:
            if ticker not in ls_longs.union(ls_short):
                self.order_target_percent(data=ticker, target=0)
                self.log(f"{ticker}, CLOSING ORDER CREATED")

        # Set target percentage of porfolio to invest into. X % of the porfolio will be 
        # divided equally among the N position or short / long. Short "borrows cash" so 
        # you have another X % of "borrowed money" for short here. 
        short_target = -1 / max(self.p.n_positions, n_short)
        longs_target = 1 / max(self.p.n_positions, n_longs)

        # Take or exit the position. If (data:=str) it will automatically get the ticker data. 
        # The target percent here indicates the percentage of porfolio to invest into. 
        for ticker in ls_short:
            self.order_target_percent(data=ticker, target=short_target)
            self.log("{ticker}, SHORT ORDER CREATED")
        for ticker in ls_longs:
            self.order_target_percent(data=ticker, target=longs_target)
            self.log("{ticker}, LONG ORDER CREATED")
