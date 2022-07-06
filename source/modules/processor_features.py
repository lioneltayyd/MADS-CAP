# Python module. 
import os, re, functools 
import pandas as pd 
from typing import Callable, Set, Tuple, List, Dict, Optional 

# Custom configs. 
from source.modules.manage_files import ManageFiles 
from source.config_py.config import (
    MERGE_FEATURE_FILENAMES, MERGE_EVENT_FILENAMES, TICKER_DATE_COLLECT, 
    TICKER_TO_COLLECT, TICKER_TO_EXCLUDE 
)



# %%
# For reading and loading files. 
manage_files = ManageFiles() 

# Date range. 
date_beg, date_end = TICKER_DATE_COLLECT 
year_beg, year_end = int(date_beg[:4]), int(date_end[:4])



# %% 
def compile_features_each_ticker(
    compile_func:Callable, 
    filepath:str, 
    ticker_to_collect:Set[str], 
    ticker_to_exclude:Set[str]=TICKER_TO_EXCLUDE, 
    load_cache:bool=True, 
    **kwargs, 
) -> pd.DataFrame: 

    '''Consolidate the features for each ticker.'''

    cache_exist = os.path.isfile(filepath) 
    df_compiled = pd.DataFrame() 
    
    # Load cache if users want to. 
    compiled_ticker = set() 
    if load_cache and cache_exist: 
        df_compiled = pd.read_csv(filepath) 
        compiled_ticker = set(df_compiled["ticker"].to_list()) 

    # Track the total number of ticker to collect. 
    ticker_to_collect = ticker_to_collect.difference(ticker_to_exclude).difference(compiled_ticker) 
    save_round, max_len = 5, len(ticker_to_collect) - 1 

    # Modify the default arguments for the (rank_func). 
    func = functools.partial(compile_func, **kwargs) 

    for i, ticker in enumerate(ticker_to_collect): 
        # Skip the API call if users want to load the cache and the ticker already exists. 
        if compiled_ticker and ticker in compiled_ticker: 
            print(f"Data already exists. Skipped ({ticker}).") 
            continue 
        
        # Get feature data for each ticker and consolidate them. 
        df = func(ticker) 
        df_compiled = pd.concat([df_compiled, df], axis="index", join="outer", ignore_index=True) 

        # Save the data at every N round iteration. 
        if i % save_round == 0 or max_len - i < save_round: 
            df_compiled.to_csv(filepath, index=False) 
            print(f"Save to ({filepath}).") 

    return df_compiled 



# %%
def concat_eventdates(event_filenames:Dict[str,str]=MERGE_EVENT_FILENAMES) -> pd.DataFrame: 
    '''Concat all the event dates from various datasets.''' 

    df_eventdates = pd.DataFrame() 

    # Read, sort the dates to ensure it's in order, then consolidate all datasets. 
    for filename, dirpath in event_filenames.items(): 
        df_dates = manage_files.pd_read_from(dirpath, filename) 
        df_dates.sort_values(by=df_dates.columns.to_list(), inplace=True) 
        df_eventdates = pd.concat([df_eventdates, df_dates], axis="columns") 
        
    return df_eventdates 



# %% 
def add_eventflags(df:pd.DataFrame, eventdates:pd.DataFrame) -> pd.DataFrame:
    '''Add flags for each event according to matching rows in ticker data.'''

    for colname in eventdates.columns: 
        df[colname] = 0 

        # Ensure the datetime is converted to str to be able to match dates. 
        df["date"], eventdates[colname] = df["date"].astype(str), eventdates[colname].astype(str) 
        
        # Flag matching dates with 1. 
        boo_dates = df["date"].isin(eventdates[colname].values) 
        df.loc[boo_dates, colname] = 1 

    return df 



# %%
def concat_eachyear(
    dirpath:str, 
    keep_tickers:Set[str]=TICKER_TO_COLLECT, 
    keep_cols:Optional[List[str]]=list(), 
    drop_cols:Optional[List[str]]=list(), 
    yearrange:Tuple[int,int]=(year_beg, year_end) 
) -> pd.DataFrame: 
    '''Concat all the datasets from different years.''' 

    df_allyear = pd.DataFrame() 
    keep_tickers = keep_tickers.difference(TICKER_TO_EXCLUDE) 

    # Define the range of year to get the data from. 
    year_beg, year_end = yearrange 
    yearrange = set(range(year_beg, year_end + 1, 1)) 

    # Read, filter tickers and columns, then consolidate all datasets. 
    for filename in os.listdir(dirpath): 
        
        # Extract the year from the filename to check if it's within the year range. 
        found_year = re.findall(r".+_(\d{4})\.\w+$", filename) 

        if found_year and int(found_year[0]) in yearrange: 
            df_peryear = manage_files.pd_read_from(dirpath, filename) 

            # Filter columns. 
            keep_cols = keep_cols if keep_cols else df_peryear.columns.difference(drop_cols) 
            df_peryear = df_peryear.loc[df_peryear["ticker"].isin(keep_tickers), keep_cols] 

            # Consolidate the datasets for each year. 
            df_allyear = pd.concat([df_allyear, df_peryear], axis="index") 

    return df_allyear 



# %%
def merge_with_ticker(
    df:pd.DataFrame, 
    merge_with:pd.DataFrame, 
    merge_suffix:str="", 
    merge_on:List[str]=["date"], 
    relation:str="many_to_one" 
) -> pd.DataFrame:
    '''
    Merge features with ticker data. Merge date format should be (YYYY-MM-DD). 
    '''

    # Ensure the datetime is converted to str to be able to match dates. 
    df["date"], merge_with["date"] = df["date"].astype(str), merge_with["date"].astype(str) 

    # Rename columns. 
    merge_with.columns = [f"{merge_suffix}_{c}" for c in merge_with.columns] 
    right_on = [f"{merge_suffix}_{c}" for c in merge_on] 

    # Merge on (date) column. 
    df_merged = df.merge(
        right=merge_with, how="left", left_on=merge_on, right_on=right_on, validate=relation
    ) 

    # # Convert back to datetime. 
    # df_merged["date"] = pd.to_datetime(df_merged["date"], infer_datetime_format=True) 

    return df_merged 
