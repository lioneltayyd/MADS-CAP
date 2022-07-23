# Python module. 
import os, math, re 
import numpy as np 
import pandas as pd 
import functools 
from typing import Callable, Dict, List, Tuple, Any 
from alpha_vantage.fundamentaldata import FundamentalData 

# Custom configs. 
from source.config_py.config import (
    FINANCIAL_KEEP_FEATURES, 
    FINANCIAL_COMPUTE_CHANGE, FINANCIAL_COMPUTE_COMBINATION, 
    FINANCIAL_COMPUTE_RATIO, FINANCIAL_EVAL_QUALITY, 
)



# %%
# Load Alpha Vantage object. 
datasource = FundamentalData(os.environ["ALPHA_VANTAGE_API_SECRET"], output_format="pandas") 



# %%
def get_snp_wikiinfo() -> pd.DataFrame: 
    '''
    Get S&P sector info from Wikipedia. 
    '''
    
    print(f"Getting S&P sector info from (Wikipedia).") 

    # Get the S&P sector info. 
    df_snp_info = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")[0] 
    df_snp_info.columns = [re.sub(r"\s|-", "_", c).lower() for c in df_snp_info.columns] 
    df_snp_info.rename(columns={"symbol": "ticker"}, inplace=True) 

    return df_snp_info 



# %%
def get_corporate_overview_alphav(ticker:str) -> pd.DataFrame: 
    '''
    Get corporate and stock info from Alpha Vantage. 

    –   Check the cost for the API request here: https://www.alphavantage.co/premium/
        Free version offers only 5 API calls per minute. 
    –   You can search the ticker via: https://www.buyupside.com/alphavantagelive/searchforsymboluser.php 
        Caution: facebook's ticker is META, not FB, but in wikipedia still use FB. 
    '''
    
    print(f"Getting corporate and stock info from (Alpha Vantage) for ({ticker}).") 

    # Get the corporate info. 
    df_corp_overview = datasource.get_company_overview(ticker)[0] 
    df_corp_overview.rename(columns={"Symbol": "ticker"}, inplace=True) 

    return df_corp_overview



# %%
def get_fundamental_alphav(ticker:str, annual:bool=True) -> pd.DataFrame: 
    '''
    Get fundamental data from Alpha Vantage. 

    –   Check the cost for the API request here: https://www.alphavantage.co/premium/
        Free version offers only 5 API calls per minute. 
    –   You can search the ticker via: https://www.buyupside.com/alphavantagelive/searchforsymboluser.php 
        Caution: facebook's ticker is META, not FB, but in wikipedia still use FB. 
    '''
    
    frequency = "annually" if annual else "quarterly" 
    print(f"Getting fundamental ({frequency}) data from (Alpha Vantage) for ({ticker}).") 
    
    df_report_compiled = pd.DataFrame()

    # Get the financial statement. 
    if annual: 
        dict_report = {
            "is_state": datasource.get_income_statement_annual(ticker)[0], 
            "bs_state": datasource.get_balance_sheet_annual(ticker)[0], 
            "cf_state": datasource.get_cash_flow_annual(ticker)[0], 
        }
    else: 
        # Get the financial statement. 
        dict_report = {
            "is_state": datasource.get_income_statement_quarterly(ticker)[0], 
            "bs_state": datasource.get_balance_sheet_quarterly(ticker)[0], 
            "cf_state": datasource.get_cash_flow_quarterly(ticker)[0], 
        }

    # Merge the financial statements. 
    getcol = ["fiscalDateEnding", "reportedCurrency"] 
    for i, df_report in enumerate(dict_report.values()): 
        None if i == 0 else df_report.drop(columns=getcol, inplace=True) 
        df_report_compiled = df_report_compiled.merge(right=df_report, how="outer", left_index=True, right_index=True) 

    # Replace all (None) string to (np.NaN) object and convert numeric columns to numeric dtype. 
    getcol = df_report_compiled.columns.difference(getcol) 
    df_report_compiled[getcol] = df_report_compiled[getcol].apply(pd.to_numeric, errors="coerce", axis=0) 

    # Track the ticker. 
    df_report_compiled["ticker"] = ticker 

    # Rearrange columns. 
    df_report_compiled = df_report_compiled.loc[:, ["ticker"] + df_report_compiled.columns[:-1].to_list()] 

    # Sort the by report date. 
    df_report_compiled.sort_values(by="fiscalDateEnding", ascending=True, inplace=True) 

    # Drop rows with empty date. 
    df_report_compiled.dropna(axis="index", subset=["fiscalDateEnding"], inplace=True) 

    return df_report_compiled 



# %% 
def compute_extra_fundamental(
    df:pd.DataFrame, 
    keep_features:List[str]=FINANCIAL_KEEP_FEATURES, 
    compute_change: Dict[str,str]=FINANCIAL_COMPUTE_CHANGE, 
    compute_combination: Dict[str,Dict[str,List[str]]]=FINANCIAL_COMPUTE_COMBINATION, 
    compute_ratio: Dict[str,List[str]]=FINANCIAL_COMPUTE_RATIO 
) -> pd.DataFrame: 
    '''Compute change / growth rate, arithmetic, and ratio to create additional fundamental data.'''
    
    print("Compute additional fundamental data.") 

    df_proc = df[keep_features].copy() 

    # Compute change or growth rate. 
    for outcol, computecol in compute_change.items(): 
        df_proc[outcol] = df_proc.groupby("ticker")[computecol].pct_change(periods=1) 

    # Compute arithmetic. 
    for outcol, dict_compute in compute_combination.items(): 
        df_proc[outcol] = 0 
        for computecol in dict_compute["add"]: 
            df_proc[outcol] += df_proc[computecol] 
        for computecol in dict_compute["sub"]: 
            df_proc[outcol] -= df_proc[computecol].abs() 

    # Compute ratio. 
    for outcol, computecols in compute_ratio.items(): 
        numcol, dencol = tuple(computecols) 
        df_proc[outcol] = df_proc[numcol] / df_proc[dencol] 

    return df_proc 



# %% 
def score_fundamental(df:pd.DataFrame, eval_method:Dict[str,Dict[str,Any]]=FINANCIAL_EVAL_QUALITY) -> pd.DataFrame: 
    '''Score the company or ticker by the fundamental quality.'''
    
    # Compute score. 
    dict_func = eval_method[df.name] 
    score = eval(f'''{dict_func["func"]}(df, **{dict_func["param"]})''') 

    if np.isnan(score) or math.inf == abs(float(score)): 
        return np.NaN 

    # Evaluate the score. 
    meet_criteria = eval(str(score) + " " + dict_func["benchmark"]) 
    meet_criteria = 1 * dict_func["weightage"] if meet_criteria else 0 

    return meet_criteria 



# %% 
def rank_fundamental(
    rank_func:Callable, 
    df:pd.DataFrame, 
    eval_method:Dict[str,Dict[str,Any]]=FINANCIAL_EVAL_QUALITY
) -> pd.DataFrame: 
    '''Rank the company or ticker by the fundamental quality.'''

    print(f"Ranking the fundamental quality.") 

    # Modify the default arguments for the (rank_func). 
    func = functools.partial(rank_func, eval_method=eval_method) 

    # Compute the score for each fundamental metric. 
    agg_funcs = [f'''score_{c}=pd.NamedAgg(column="{c}", aggfunc=func)''' for c in FINANCIAL_EVAL_QUALITY.keys()] 
    agg_funcs = ", ".join(agg_funcs) 
    df_rank = eval(f'''df.groupby("ticker").agg({agg_funcs})''') 

    # Sum the score and sort it. 
    df_rank["total_score"] = df_rank.sum(axis="columns") 
    df_rank["rank_quantl"] = df_rank["total_score"].rank(method="average", ascending=False, pct=True) 

    # Rank the score. 
    df_rank = df_rank \
        .sort_values(by=["rank_quantl"], ascending=True) \
        .reset_index(drop=False) 

    return df_rank 



# %% 
def within_sector_diff(
    df:pd.DataFrame, 
    sector_info:pd.DataFrame, 
    usecols:List[str], 
    yearspec:Tuple[str,int], 
    groupcols:List[str]
) -> pd.DataFrame: 
    '''Score the company or ticker by the performance difference within sector.''' 
    
    yearcol, year = yearspec 

    # Merge fundamental data with sector info. 
    df = df.merge(right=sector_info, on="ticker", how="left", suffixes=(None, "_info")).loc[:, usecols] 

    # Extract numerical and categorical columns. 
    numcols = df.select_dtypes(include="number").columns.to_list() 
    catcols = df.columns.difference(numcols).to_list() 

    # Convert to datetime if not it's not. 
    if not np.issubdtype(df[yearcol].dtype, np.datetime64): 
        df[yearcol] = pd.to_datetime(df[yearcol], infer_datetime_format=True) 

    # Filter by date. 
    df_datefil = df.loc[df[yearcol].dt.year == year].copy() 
    df_datefil = df_datefil.set_index(catcols) 

    # Compare the performance difference within sector. 
    df_groupag = df_datefil.groupby(groupcols).transform("mean") 
    df_diffval = df_datefil - df_groupag 
    df_diffval.reset_index(drop=False, inplace=True) 

    return df_diffval



# %% 
def rank_within_sector_diff(df:pd.DataFrame, groupcols:List[str]) -> pd.DataFrame: 
    '''Rank the company or ticker by the performance difference within sector.'''

    print(f"Ranking the performance difference within sector.") 

    # Extract numerical and categorical columns. 
    numcols = df.select_dtypes(include="number").columns.to_list() 
    catcols = df.columns.difference(numcols).to_list() 

    # Rank the differences. 
    df_rank = df \
        .set_index(catcols) \
        .groupby(groupcols) \
        .rank(method="average", pct=False, ascending=False) \
        .sum(axis="columns") \
        .groupby(groupcols) \
        .rank(method="average", pct=True, ascending=False) \
        .reset_index(drop=False) 

    df_rank.columns = catcols + ["rank_quantl"] 
    df = df.merge(right=df_rank[["ticker", "rank_quantl"]], on="ticker", how="left") 

    return df 
