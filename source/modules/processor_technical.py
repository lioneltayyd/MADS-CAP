# Python module. 
import os, talib 
import pandas as pd 
from alpha_vantage.techindicators import TechIndicators 
from typing import Tuple, List, Dict 


# Custom configs. 
from source.config_py.config import (
    TICKER_DATE_COLLECT, TECHNIND_FEATURES, CANDLESTICK_FEATURES
)



# %%
# Load Alpha Vantage object. 
datasource = TechIndicators(os.environ["ALPHA_VANTAGE_API_SECRET"], output_format="pandas") 



# %%
def get_techind_alphav(
    ticker:str, 
    features:Dict[str,Dict]=TECHNIND_FEATURES, 
    daterange:Tuple[str,str]=TICKER_DATE_COLLECT
) -> pd.DataFrame: 
    '''
    Get technical indicator data from Alpha Vantage. 

    –   Check the cost for the API request here: https://www.alphavantage.co/premium/
        Free version offers only 5 API calls per minute. 
    –   You can search the ticker via: https://www.buyupside.com/alphavantagelive/searchforsymboluser.php 
        Caution: facebook's ticker is META, not FB, but in wikipedia still use FB. 
    '''
    
    print(f"Getting technical indicator data from (Alpha Vantage) for ({ticker}).") 

    df_techind_compiled = pd.DataFrame(index=pd.date_range(daterange[0], daterange[1], freq="D")) 

    # Get the technical indicator. 
    dict_techind = {f: f'''datasource.get_{f}("{ticker}", **{p})[0]''' for f, p in features.items()} 

    # Concat the technical indicators. 
    for techname, tech_ind in dict_techind.items(): 
        df_tech_ind = eval(tech_ind) 
        df_tech_ind.columns = [f"{techname}_{c}" for c in df_tech_ind.columns] 
        df_techind_compiled = df_techind_compiled.merge(
            right=df_tech_ind, how="outer", left_index=True, right_index=True 
        ) 

    # Drop all NaN rows. 
    df_techind_compiled = df_techind_compiled.dropna(axis="index", how="all") 

    # Get date column. 
    df_techind_compiled.reset_index(drop=False, inplace=True) 
    df_techind_compiled.rename(columns={"index": "date"}, inplace=True) 

    # Track the ticker. 
    df_techind_compiled["ticker"] = ticker 

    # Rearrange columns. 
    df_techind_compiled = df_techind_compiled.loc[:, ["ticker"] + df_techind_compiled.columns[:-1].to_list()] 

    return df_techind_compiled 



# %% 
def get_candlesticks(df:pd.DataFrame, features:List[str]=CANDLESTICK_FEATURES) -> pd.DataFrame: 
	'''Get candlesticks data.''' 

	for feature in features: 
		open, high, low, close = df["open"], df["high"], df["low"], df["close"] 
		df[f"candle_{feature.lower()}"] = eval(f'''talib.{feature}(open, high, low, close)''') 

	return df 
