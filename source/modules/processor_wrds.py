# Python module. 
import wrds 
import pandas as pd 



# %%
# Initiate connection to WRDS. 
conn = wrds.Connection() 



# %%
def get_rp_sentiment(ticker:str, year:int) -> pd.DataFrame: 
    '''Get sentiment data from WRDS RavenPack.'''

    print(f"Getting sentiment data from (WRDS RavenPack) for ({ticker}, {year}).") 

    # Query the WRDS database. 
    df = conn.raw_sql(
        f'''
        SELECT *
        FROM rpna.dj_equities_{year} 
        WHERE company = 'US/{ticker}' 
        ''',  
        date_cols=["rpna_date_utc", "timestamp_utc"], 
    ) 

    # Track the ticker. 
    df["ticker"] = ticker 

    return df 



# %%
def get_compustat_fundamental(ticker:str, year_beg:int) -> pd.DataFrame: 
    '''Get sentiment data from WRDS RavenPack.'''

    print(f"Getting fundamental data from (WRDS Compustat) for ({ticker}, {year_beg} and above).") 

    # Query the WRDS database. 
    df = conn.raw_sql(
        f'''
        SELECT *
        FROM comp.funda
        WHERE tic = '{ticker}' 
        AND datadate >= '01/01/{year_beg}'
        ''',  
        date_cols=["datadate"], 
    ) 

    # Track the ticker. 
    df.rename(columns={"tic": "ticker"}, inplace=True) 

    return df 
