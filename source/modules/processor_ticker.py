# Python module. 
import numpy as np 
import pandas as pd 
import yfinance as yf
from typing import Tuple, List 



# %%
def get_ticker_yfinance(ticker:str, date_beg:str, date_end:str) -> pd.DataFrame: 
    '''
    Get ticker data from Yahoo Finance. 
    '''

    print(f"Getting ticker data from (Yahoo Finance) for ({ticker}).") 

    # Get the ticker history data. 
    df_ticker = yf \
        .Ticker(ticker) \
        .history(period="max", interval="1d", start=date_beg, end=date_end, auto_adjust=True, rounding=True) \
        .reset_index(drop=False) 

    # Rename the columns. 
    df_ticker.columns = [c.lower().replace(" ", "_") for c in df_ticker.columns] 

    # Track the ticker. 
    df_ticker["ticker"] = ticker 

    return df_ticker 



# %% 
def compute_forward_return(
    df:pd.DataFrame, 
    returns_lags:List[str]=[1,5,10,21,126,252], 
    trim_out:float=0.0001, 
    window:int=252, 
    autocorr_lags:List[str]=[1,2,3], 
    volt_range:Tuple[int]=(.25, 1.0) 
) -> pd.DataFrame: 
    '''
    Compute the forward price return (logret), volatility class (volt), mean reversion (tscore). 

    Then compute the lag for various period (1, 5, 10, 21, 126, 252). 
        - 1   == 1-day forward. 
        - 5   == 1-week forward. 
        - 10  == 2-week forward. 
        - 21  == 1-month forward. 
        - 126 == 6-month forward. 
        - 252 == 12-month forward. 
    ''' 

    # Rolling window and min period. 
    window_avg, window_std = window, window 
    period_avg, period_std = window, window 

    # Market movement / volatility scale. 
    volt_lo, volt_hi = volt_range 

    # Return categories. 
    # 	– c2c == close to close 
    # 	– o2c == open to close (price change during market opening). 
    # 	– c2o == close to open (gapping during market closing). 
    return_cats = {
        "return_c2c": lambda x: np.log(x["close"]) - np.log(x["close"].shift(lag)), 

        # # Comment out this. Not applicable beyond 1-day forward. 
        # "return_o2c": lambda x: np.log(x["close"]) - np.log(x["open"]), 
        # "return_c2o": lambda x: np.log(x["open"].shift(-1)) - np.log(x["close"]), 
    } 

    # Create labels for each ticker symbol. 
    for ticker in df["ticker"].unique(): 
        print(f"Compute forward return for ({ticker}).") 

        for keyname in return_cats.keys(): 
            
            for lag in returns_lags: 
                return_cat = keyname.split("_")[-1] 

                retname = f"{keyname}_lag{lag}" 
                tscname = f"tscore_{return_cat}_lag{lag}" 
                vltname = f"volt_{return_cat}_lag{lag}" 

                # Compute the ticker price return. 
                df[retname] = df \
                    .groupby(["ticker"])["close"] \
                    .pct_change(periods=lag) \
                    .pipe(lambda x: x.clip(lower=x.quantile(trim_out), upper=x.quantile(1 - trim_out))) \
                    .add(1) \
                    .pow(1 / lag) \
                    .sub(1) 

                # Compute the tscore for price change. 
                ret_ravg = df \
                    .groupby(["ticker"])[retname] \
                    .rolling(window=window_avg, min_periods=period_avg, win_type=None) \
                    .mean() \
                    .reset_index(drop=True) 
                ret_rstd = df \
                    .groupby(["ticker"])[retname] \
                    .rolling(window=window_std, min_periods=period_std, win_type=None) \
                    .std(ddof=1) \
                    .reset_index(drop=True) 
                df[tscname] = (df[retname] - ret_ravg) / ret_rstd 
                
                # # NOTICE: Considering... Might not needed. 
                # # Define the volatility or price movement scale or class. 
                # df[vltname] = 1 
                # df.loc[df[tscname].abs() >= volt_hi, vltname] = 2 
                # df.loc[df[tscname].abs() <= volt_lo, vltname] = 0 

                # Create autocorrsselated features for the past N days. 
                for autolag in autocorr_lags: 
                    df[f"{retname}_autolag{autolag}"] = df.groupby(["ticker"])[retname].shift(autolag) 
                    df[f"{tscname}_autolag{autolag}"] = df.groupby(["ticker"])[tscname].shift(autolag) 

                    # # NOTICE: Considering... Might not needed. 
                    # df[f"{vltname}_autolag{autolag}"] = df.groupby(["ticker"])[vltname].shift(autolag) 

    return df 
