# Python module. 
import os, re 
import pandas as pd 
from typing import Dict, Tuple, Any 
from fredapi import Fred 

# Custom configs. 
from source.config_py.config import (
    TICKER_DATE_COLLECT, ECONOMIC_FREQ
)



# %%
# Date range. 
date_beg, date_end = TICKER_DATE_COLLECT 

# Load Alpha Vantage object. 
datasource = Fred(api_key=os.environ["FRED_API_SECRET"]) 



# %%
def get_econometric_fred(
    econometric:str, 
    parameters:Dict[str,str], 
    daterange:Tuple[str,str]=(date_beg, date_end)
) -> pd.DataFrame: 
    '''
    Get econometric from FRED. 
    '''
    
    print(f"Getting FRED economic data for ({econometric}).") 

    year_beg, year_end = daterange 

    df_econometric = datasource \
        .get_series(observation_start=year_beg, observation_end=year_end, **parameters) \
        .reset_index(drop=False) 

    df_econometric.columns = ["date", "value"] 
    df_econometric["econometric"] = econometric 
    df_econometric["frequency"] = ECONOMIC_FREQ[parameters["frequency"]] 

    return df_econometric 
