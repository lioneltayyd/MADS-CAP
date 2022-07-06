import optuna 
import xgboost as xgb
from sklearn.linear_model import ElasticNet 



# -------------------------------------------------------
# Define directory and file paths 
# -------------------------------------------------------

# Define root directory. 
DIR_ROOT = "MADS-CAP"

# Directory path for saving and loading files. 
DIR_DATASET = "dataset" 
DIR_DATASET_CONSOLIDATED = f"{DIR_DATASET}/consolidated_feature" 
DIR_DATASET_TICKER = f"{DIR_DATASET}/tickers" 
DIR_DATASET_ECONOMIC_DATA = f"{DIR_DATASET}/economic_data" 
DIR_DATASET_ECONOMIC_REPORT = f"{DIR_DATASET}/economic_report" 
DIR_DATASET_OBSERVANCE = f"{DIR_DATASET}/observance" 
DIR_DATASET_FUNDAMENTAL = f"{DIR_DATASET}/fundamental" 
DIR_DATASET_GEOPOLITIC = f"{DIR_DATASET}/geopolitic" 
DIR_DATASET_TECH_IND = f"{DIR_DATASET}/technical" 
DIR_DATASET_SENTIMENT = f"{DIR_DATASET}/sentiment" 
DIR_DATASET_UTIL = f"{DIR_DATASET}/util" 
DIR_DATASET_WRDS_RAVENPACK = f"{DIR_DATASET}/wrds_ravenpack" 
DIR_DATASET_WRDS_COMPUSTAT = f"{DIR_DATASET}/wrds_compustat" 

# Directory path for saving and loading models. 
DIR_MLMODEL = "model" 
DIR_MLMODEL_MLESTIM = f"{DIR_MLMODEL}/mktmv_estimator" 

# Define the datasets you want to or merge with as features 
# for the ticker data. These events should only contain the
# date of occurances. 
MERGE_EVENT_FILENAMES = {
	# # Filename == keyname. Directory path == value. 

	"economic_reported_date.csv": DIR_DATASET_ECONOMIC_REPORT, 
	"firsttrdrday_ofmonth.csv": DIR_DATASET_OBSERVANCE, 
	"observance_dates_ext.csv": DIR_DATASET_OBSERVANCE, 
	"santa_rally.csv": DIR_DATASET_OBSERVANCE, 
	"triple_witching_week.csv": DIR_DATASET_OBSERVANCE, 
	# "geopolitic_dates.csv": DIR_DATASET_GEOPOLITIC, 
} 

# Define the datasets you want to or merge with as features 
# for the ticker data. These features should contain numerical 
# and other types of data in addition to dates. 
MERGE_FEATURE_FILENAMES = {
	# # Filename == keyname. Directory path == value. 

	"economic_reported_data.csv": DIR_DATASET_ECONOMIC_REPORT, 
	"fred__dataframes_bond_yield.csv": DIR_DATASET_ECONOMIC_DATA, 
	"fred__dataframes_business.csv": DIR_DATASET_ECONOMIC_DATA, 
	"fred__dataframes_employment.csv": DIR_DATASET_ECONOMIC_DATA, 
	"fred__dataframes_gov_fiscal.csv": DIR_DATASET_ECONOMIC_DATA, 
	"fred__dataframes_household.csv": DIR_DATASET_ECONOMIC_DATA, 
	"fred__dataframes_housing.csv": DIR_DATASET_ECONOMIC_DATA, 
	"fred__dataframes_manufacturer.csv": DIR_DATASET_ECONOMIC_DATA, 
	"fred__dataframes_monetary.csv": DIR_DATASET_ECONOMIC_DATA, 
	"fred__dataframes_price.csv": DIR_DATASET_ECONOMIC_DATA, 
	"quan__dataframes_manufacturer.csv": DIR_DATASET_ECONOMIC_DATA, 
	"quan__dataframes_others.csv": DIR_DATASET_ECONOMIC_DATA, 
	"ravenpack_sentiment_2010.csv": DIR_DATASET_SENTIMENT, 
	"ravenpack_sentiment_2011.csv": DIR_DATASET_SENTIMENT, 
	"ravenpack_sentiment_2012.csv": DIR_DATASET_SENTIMENT, 
	"ravenpack_sentiment_2013.csv": DIR_DATASET_SENTIMENT, 
	"ravenpack_sentiment_2014.csv": DIR_DATASET_SENTIMENT, 
	"ravenpack_sentiment_2015.csv": DIR_DATASET_SENTIMENT, 
	"ravenpack_sentiment_2016.csv": DIR_DATASET_SENTIMENT, 
	"ravenpack_sentiment_2017.csv": DIR_DATASET_SENTIMENT, 
	"ravenpack_sentiment_2018.csv": DIR_DATASET_SENTIMENT, 
	"ravenpack_sentiment_2019.csv": DIR_DATASET_SENTIMENT, 
	"ravenpack_sentiment_2020.csv": DIR_DATASET_SENTIMENT, 
	"ravenpack_sentiment_2021.csv": DIR_DATASET_SENTIMENT, 
	"ravenpack_sentiment_2022.csv": DIR_DATASET_SENTIMENT, 
	"technical_indicator.csv": DIR_DATASET_TECH_IND, 
} 

# -------------------------------------------------------
# Define the ticker symbol to collect 
# -------------------------------------------------------

# Define the starting and ending date when collecting the ticker data. 
TICKER_DATE_COLLECT = "1998-12-01", "2022-02-28" 

# Define whether to collect the 500 stocks from S&P. 
# We will use this only prior to the filtering stage. 
# Once they are filtered, pick the top N tickers and 
# assign them to (TICKER_TO_COLLECT) variable. 
TICKER_FROM_SNP = True 

# Define the list of tickers we are interested to investigate on. 
TICKER_TO_COLLECT = set([
	# # Semiconductor. 
	"AAPL", "NVDA", "AMD", 
	# # Tech in general. 
	"AMZN", "GOOGL", "MSFT", 
	# # Discretionary. 
	"TSLA", "NKE", 
	# # Staple. 
	"HD", "LOW", "KO", "MCD", 
	# # Entertainment. 
	"NFLX", "DIS", 
	# # Energy. 
	"DVN", "CVX", "COP", 
	# # Aerospace. 
	"BA", "LMT", "NOC", "HON", 
	# # Industrial. 
	"J", "CAT", "DOW", 
	# # Financial banking. 
	"C", "JPM", "PYPL", 
	# # Financial service. 
	"MA", "V", "AXP", 
	# # Communication. 
	"VZ", 
	# # Drugs maker. 
	"MRK", "JNJ", 
]) 

# Define ticker to exclude from S&P. Exclude them because of API error. 
TICKER_TO_EXCLUDE = set([
	"ANTM", 
])

# -------------------------------------------------------
# Define the dates for market turmoil period 
# -------------------------------------------------------

# Recession, crisis, correction, bear market, bubble, significant event, ... 
# Check out 
# 	- https://en.wikipedia.org/wiki/List_of_stock_market_crashes_and_bear_markets 
# 	- https://en.wikipedia.org/wiki/Yield_curve 
# 	- https://en.wikipedia.org/wiki/List_of_economic_crises 

RECESSION_PERIOD = [
	("Covid 2019", "2020-02-01", "2020-04-01"),
	("DebtCrisis 2008", "2007-11-01", "2009-06-01"),
	("DotCom 2001", "2001-03-01", "2001-11-01"),
	("R 1990", "1990-07-01", "1991-03-01"),
	("R 1982", "1981-11-01", "1982-07-01"),
	("R 1980", "1980-01-01", "1980-07-01"),
	("R 1974", "1973-11-01", "1975-03-01"),
	("R 1970", "1969-12-01", "1970-11-01"),
	("R 1960", "1960-04-01", "1961-02-01"),
	("R 1957", "1957-08-01", "1958-04-01"),
	("R 1953", "1953-07-01", "1954-05-01"),
	("R 1949", "1948-11-01", "1949-10-01"),
]

# Yield curve inversion period (10Y over 3M Treasury Yield). 
# Check out: 
# 	- https://en.wikipedia.org/wiki/Yield_curve 

YIELD_CURVE_INVERSION = [

]

# -------------------------------------------------------
# Define the economic data to collect 
# -------------------------------------------------------

ECONOMIC_FRED_FEATURES = {
	# # Monetary policy. 
	"fed_ffr": dict(
		series_id="FEDFUNDS",
		units="lin",
		frequency="m",
		aggregation_method="avg"
	), 
	"mortgage_rate_30yr": dict(
		series_id="MORTGAGE30US",
		units="lin",
		frequency="m",
		aggregation_method="avg"
	), 
	"mortgage_rate_15yr": dict(
		series_id="MORTGAGE15US",
		units="lin",
		frequency="m",
		aggregation_method="avg"
	), 
	"prime_loan_rate": dict(
		series_id="DPRIME",
		units="lin",
		frequency="m",
		aggregation_method="avg"
	), 

	# # Bond yield. 
	"bond_yield_3mo": dict(
		series_id="DGS3MO",
		units="lin",
		frequency="m",
		aggregation_method="avg"
	), 
	"bond_yield_2yr": dict(
		series_id="DGS2",
		units="lin",
		frequency="m",
		aggregation_method="avg"
	), 
	"bond_yield_5yr": dict(
		series_id="DGS5",
		units="lin",
		frequency="m",
		aggregation_method="avg"
	), 
	"bond_yield_10yr": dict(
		series_id="DGS10",
		units="lin",
		frequency="m",
		aggregation_method="avg"
	), 
	"bond_yield_30yr": dict(
		series_id="DGS30",
		units="lin",
		frequency="m",
		aggregation_method="avg"
	), 
	"bond_yield_10yr_minus_ffr": dict(
		series_id="T10YFF",
		units="lin",
		frequency="m",
		aggregation_method="avg"
	), 
	"bond_yield_10yr_minus_3mo": dict(
		series_id="T10Y3M",
		units="lin",
		frequency="m",
		aggregation_method="avg"
	), 
	"bond_yield_10yr_minus_2yr": dict(
		series_id="T10Y2Y",
		units="lin",
		frequency="m",
		aggregation_method="avg"
	), 
} 

# ECONOMIC_FRED_FEATURES = {
#     "employment": [
#         "unemployment_rate",
#         "unemployment_natural_rate",
#     ], 
#     "household": [
#         "personal_dispensable_income_yoy",
#         "personal_consumption_yoy",
#         "personal_consumption_real_yoy",
#         "personal_consumption_ex_food_energy_yoy",
#     ], 
#     "manufacturer": [
# 		"industry_production_mom", 
# 		"capacity_utilisation", 
# 		"manufacturer_production_mom", 
# 		"manufacturer_new_order_yoy", 
# 		"manufacturer_new_order_mom", 
# 		"manufacturer_new_order_ex_def_yoy", 
# 		"manufacturer_new_order_ex_def_mom", 
# 		"manufacturer_new_order_ex_trans_yoy", 
# 		"manufacturer_new_order_ex_trans_mom", 
# 		"manufacturer_inventory_sales_ratio", 
#     ], 
#     "business": [
#         "online_sales_yoy",
#         "retail_sales_yoy",
#         "retail_sales_ex_auto_yoy", 
#         "vehicle_sales_yoy",
#         "business_inventory_sales_ratio",
#         "retail_inventory_sales_ratio",
#     ], 
#     "housing": [
#         "housing_starts",
#         "housing_starts_yoy",
#         "building_permit",
#         "new_home_sales",
#         "new_home_sales_yoy",
#     ], 
#     "gov_fiscal": [
#         "gdp_us_qoq",
#         "gdp_us_yoy",
#         "gdp_real_us_qoq", 
#         "gdp_real_us_yoy",
#     ], 
#     "monetary": [
#         "fed_ffr",
#         "mortgage_rate_30yr",
#         "mortgage_rate_15yr",
#         "prime_loan_rate",
#         "excess_reserve_depo",
#         "liquidity_m1_yoy",
#         "velocity_m1",
#         "liquidity_m2_yoy",
#         "velocity_m2",
#         "monetary_base", 
#     ], 
#     "price": [
#         "gdp_deflator_us_yoy",
#         "personal_consumption_deflator_yoy",
#         "consumer_cpi_yoy",
#         "consumer_cpi_ex_food_energy_yoy",
#         "producer_ppi_yoy",
#         "producer_ppi_ex_food_energy_yoy", 
#         "case_shiller_hpi",
#         "case_shiller_hpi_yoy",
#     ], 
#     "bond_yield": [
#         "bond_yield_3mo",
#         "bond_yield_2yr",
#         "bond_yield_5yr",
#         "bond_yield_10yr",
#         "bond_yield_30yr",
#         "bond_yield_10yr_minus_ffr",
#         "bond_yield_10yr_minus_3mo",
#         "bond_yield_10yr_minus_2yr",
#     ], 
# } 

# ECONOMIC_QUANT_FEATURES = {
#     "manufacturer": [
#         "ism_pmi_manufacturer",
#         "ism_pmi_services",
#     ], 
# } 

# -------------------------------------------------------
# Define the technical indicator data to collect 
# -------------------------------------------------------

# The parameters are defined here: https://github.com/RomelTorres/alpha_vantage/blob/develop/alpha_vantage/techindicators.py
TECHNIND_FEATURES = {
	# # Example. Write the function name and parameters. 
	"macd": dict(
		interval="daily", 
		series_type="close", 
		fastperiod=12, 
		slowperiod=26, 
		signalperiod=9, 
	), 
	"stoch": dict(
		interval="daily", 
		fastkperiod=5, 
		slowkperiod=3, 
		slowdperiod=0, 
		slowkmatype=3, 
		slowdmatype=0, 
	)
}

# -------------------------------------------------------
# Define candlesticks   
# -------------------------------------------------------

# Taken from (TA-Lib). 
# 	– http://mrjbq7.github.io/ta-lib/func_groups/pattern_recognition.html 

CANDLESTICK_FEATURES = [
	# "CDL2CROWS", 
	"CDL3BLACKCROWS", 
	# "CDL3INSIDE", 
	# "CDL3LINESTRIKE", 
	# "CDL3OUTSIDE", 
	# "CDL3STARSINSOUTH", 
	# "CDL3WHITESOLDIERS", 
	# "CDLABANDONEDBABY", 
	# "CDLADVANCEBLOCK", 
	# "CDLBELTHOLD", 
	# "CDLBREAKAWAY", 
	# "CDLCLOSINGMARUBOZU", 
	# "CDLCONCEALBABYSWALL", 
	# "CDLCOUNTERATTACK", 
	"CDLDARKCLOUDCOVER", 
	"CDLDOJI", 
	"CDLDOJISTAR", 
	"CDLDRAGONFLYDOJI", 
	"CDLENGULFING", 
	"CDLEVENINGDOJISTAR", 
	"CDLEVENINGSTAR", 
	# "CDLGAPSIDESIDEWHITE", 
	# "CDLGRAVESTONEDOJI", 
	"CDLHAMMER", 
	"CDLHANGINGMAN", 
	"CDLHARAMI", 
	# "CDLHARAMICROSS", 
	# "CDLHIGHWAVE", 
	# "CDLHIKKAKE", 
	# "CDLHIKKAKEMOD", 
	# "CDLHOMINGPIGEON", 
	# "CDLIDENTICAL3CROWS", 
	# "CDLINNECK", 
	"CDLINVERTEDHAMMER", 
	# "CDLKICKING", 
	# "CDLKICKINGBYLENGTH", 
	# "CDLLADDERBOTTOM", 
	# "CDLLONGLEGGEDDOJI", 
	# "CDLLONGLINE", 
	# "CDLMARUBOZU", 
	# "CDLMATCHINGLOW", 
	# "CDLMATHOLD", 
	"CDLMORNINGDOJISTAR", 
	"CDLMORNINGSTAR", 
	# "CDLONNECK", 
	# "CDLPIERCING", 
	"CDLRICKSHAWMAN", 
	# "CDLRISEFALL3METHODS", 
	# "CDLSEPARATINGLINES", 
	"CDLSHOOTINGSTAR", 
	# "CDLSHORTLINE", 
	# "CDLSPINNINGTOP", 
	# "CDLSTALLEDPATTERN", 
	# "CDLSTICKSANDWICH", 
	# "CDLTAKURI", 
	# "CDLTASUKIGAP", 
	# "CDLTHRUSTING", 
	"CDLTRISTAR", 
	# "CDLUNIQUE3RIVER", 
	# "CDLUPSIDEGAP2CROWS", 
	# "CDLXSIDEGAP3METHODS", 
] 

# -------------------------------------------------------
# Define financial statement data  
# -------------------------------------------------------

FINANCIAL_KEEP_FEATURES = [
	# # General. 
	"ticker", 
	"fiscalDateEnding", 
	# # Income statement. 
	"totalRevenue",
	"researchAndDevelopment",
	"capitalExpenditures",
	"depreciationAndAmortization",
	"grossProfit",
	"interestExpense",
	"ebit",
	"incomeBeforeTax",
	"netIncomeFromContinuingOperations",
	"netIncome_x",
	# # Balance sheet. 
	"inventory",
	"totalAssets",
	"totalCurrentAssets", 
	"totalCurrentLiabilities", 
	"totalLiabilities", 
	"longTermDebtNoncurrent", 
	"totalShareholderEquity", 
	# # Cash flow. 
	"operatingCashflow",

	# # Uncomment any of the following if you need it. 
	# # Or you can add unavailable feature to the list. 
	# # The feature you add must be a valid feature. 
] 

# For computing change or growth rate. 
# Example: "new_feature_name": "feature_name" 
FINANCIAL_COMPUTE_CHANGE = {
	# # From Jeremy Zhang Qi. 
	"growth_totalRevenue": "totalRevenue", 
	"growth_grossProfit": "grossProfit", 
	"growth_netIncomeFromOperations": "netIncomeFromContinuingOperations", 
	"growth_ebit": "ebit", 
	"growth_netIncome_x": "netIncome_x", 
	"growth_operatingCashflow": "operatingCashflow", 
}

# For computing addition and subtraction. 1st = Addition, 2nd = Subtraction 
# Example: 
#     "new_feature_name": {
#         "add": ["1st_feature_to_add", "2nd_feature_to_add"], 
#         "sub": ["1st_feature_to_substract"], 
#     },
FINANCIAL_COMPUTE_COMBINATION = {
	# # Uncomment any of the following if you want to get them. 
	# # Remember to change the variable names. 

    "ownerEarnings": {
        "add": ["netIncome_x", "depreciationAndAmortization"], 
        "sub": ["capitalExpenditures"], 
    },
    "assetsQuick": {
        "add": ["totalCurrentAssets"], 
        "sub": ["inventory"],
    },
    "workingCapital": {
        "add": ["totalCurrentAssets"], 
        "sub": ["totalCurrentLiabilities"],
    },
    "shareholderEquity": {
        "add": ["totalAssets", "totalShareholderEquity"], 
        "sub": ["totalLiabilities"],
    }
}

# For computing ratio. 
# Example: "new_feature_name": ["numerator", "denominator"] 
FINANCIAL_COMPUTE_RATIO = {
	# # From Jeremy Zhang Qi. 
    "turnover_asset": ["totalRevenue", "totalAssets"],
    "turnover_operatingCashFlow": ["operatingCashflow", "totalRevenue"],
    "margin_grossProfit": ["grossProfit", "totalRevenue"],
    "margin_netIncomeFromOperations": ["netIncomeFromContinuingOperations", "totalRevenue"],

	# # Uncomment any of the following if you want to get them. 
	# # Remember to change the variable names. 

    "workingCapitalTurnover": ["workingCapital", "totalRevenue"],
    "inventoryRatio": ["inventory", "totalRevenue"],
    "capexRatio": ["capitalExpenditures", "totalRevenue"],
    "researchAndDevelopmentRatio": ["researchAndDevelopment", "totalRevenue"],
    "incomeNetPretaxPerRevenue": ["incomeBeforeTax", "totalRevenue"],
    "currentRatio": ["totalCurrentAssets", "totalCurrentLiabilities"],
    "quickRatio": ["assetsQuick", "totalCurrentLiabilities"],
    "cashRatio": ["operatingCashflow", "totalCurrentLiabilities"],
    "longTermDebtRatio": ["longTermDebtNoncurrent", "incomeBeforeTax"],
    "cashFlowOperatingRatio": ["operatingCashflow", "totalCurrentLiabilities"],
    "interestPayRatio": ["interestExpense", "grossProfit"],
    "debtEquityRatio": ["totalLiabilities", "totalShareholderEquity"],
    "shareholderEquityRatio": ["shareholderEquity", "totalAssets"],
    "returnEquityRatio": ["ownerEarnings", "totalShareholderEquity"],
    "cashFlowOperatingPerShare": ["operatingCashflow", "totalShareholderEquity"],
}

# For evaluating and ranking corporate's fundamental quality. 
# Example: 
# 	"feature_name": {
# 		"func": "function_name", 
# 		"param": dict(arg=value), 
# 		"benchmark": ">= .03", 
# 	}, 
FINANCIAL_EVAL_QUALITY = {
	"growth_totalRevenue": {
		"func": "np.mean", 
		"param": dict(), 
		"benchmark": ">= .1", 
		"weightage": 1, 
	}, 
	"growth_grossProfit": {
		"func": "np.mean", 
		"param": dict(), 
		"benchmark": ">= .1", 
		"weightage": 1, 
	}, 
	"growth_netIncomeFromOperations": {
		"func": "np.mean", 
		"param": dict(), 
		"benchmark": ">= .1", 
		"weightage": 1, 
	}, 
	"growth_ebit": {
		"func": "np.mean", 
		"param": dict(), 
		"benchmark": ">= .1", 
		"weightage": 1, 
	}, 
	"growth_netIncome_x": {
		"func": "np.mean", 
		"param": dict(), 
		"benchmark": ">= .1", 
		"weightage": 1, 
	}, 
	"growth_operatingCashflow": {
		"func": "np.mean", 
		"param": dict(), 
		"benchmark": ">= .1", 
		"weightage": 1, 
	}, 
	"turnover_asset": {
		"func": "np.mean", 
		"param": dict(), 
		"benchmark": ">= 1.0", 
		"weightage": 1, 
	}, 
	"turnover_operatingCashFlow": {
		"func": "np.mean", 
		"param": dict(), 
		"benchmark": ">= 1.0", 
		"weightage": 1, 
	}, 
	"margin_grossProfit": {
		"func": "np.mean", 
		"param": dict(), 
		"benchmark": ">= .2", 
		"weightage": 1, 
	}, 
	"margin_netIncomeFromOperations": {
		"func": "np.mean", 
		"param": dict(), 
		"benchmark": ">= .2", 
		"weightage": 1, 
	}, 
}

# -------------------------------------------------------
# Define parameters 
# -------------------------------------------------------

PARAM_SEED = 42

# Wikifier parameters. 
PARAM_THRESHOLD = 0.8 
PARAM_LANG = "en" 

# -------------------------------------------------------
# For multiverse analysis 
# -------------------------------------------------------

# Number of trials to run the hyperparameter optimisation. 
EXPERIMENT_TRIAL = 25 

# Define different set of components. 
EXPERIMENT_COMPS = [
	["newstheme"], 
	["sentiment"], 
	["autocorrs"], 
	["newstheme", "sentiment"], 
	["autocorrs", "newstheme"], 
	["autocorrs", "sentiment"], 
	["newstheme", "sentiment", "autocorrs"], 
]

# Assign different model choices and default parameters to experiment with. 
EXPERIMENT_MODEL = {
	# ElasticNet. 
	"els": {
		"model": ElasticNet(
			alpha=1, l1_ratio=.5, max_iter=5000, random_state=PARAM_SEED
		), 
		"param_dist": {
			"l1_ratio"  : [.5, .3, .1], 
		}, 
		"bayes_opt": False, 
	}, 
	# Random Forest. 
	"rfr": {
		"model": xgb.XGBRFRegressor(
			learning_rate=1, n_estimators=100, max_depth=8, base_score=0.5, 
			colsample_bynode=.5, reg_lambda=0.1, reg_alpha=1.0, min_split_loss=0.05,
			min_child_weight=1, subsample=0.5, tree_method="auto", booster="gbtree", 
			num_parallel_tree=2, objective="reg:squarederror", eval_metric="rmse", 
			seed=PARAM_SEED, 
		), 
		"param_dist": {
			"max_depth"         : optuna.distributions.IntUniformDistribution(3, 8), 
			"n_estimators"      : optuna.distributions.IntUniformDistribution(100, 500), 
			"min_child_weight"  : optuna.distributions.IntUniformDistribution(1, 20), 
		}, 
		"bayes_opt": True, 
	}, 
	# XGBoost. 
	"xgb": {
		"model": xgb.XGBRegressor(
			learning_rate=0.001, n_estimators=100, max_depth=8, base_score=0.5, 
			reg_lambda=0.1, reg_alpha=1.0, min_split_loss=0.05, min_child_weight=1, 
			subsample=0.5, tree_method="auto", booster="gbtree", num_parallel_tree=2, 
			objective="reg:squarederror", eval_metric="rmse", seed=PARAM_SEED, 
		), 
		"param_dist": {
			"learning_rate"     : optuna.distributions.LogUniformDistribution(1e-4, 1e-2), 
			"max_depth"         : optuna.distributions.IntUniformDistribution(3, 8), 
			"n_estimators"      : optuna.distributions.IntUniformDistribution(100, 500), 
			"min_child_weight"  : optuna.distributions.IntUniformDistribution(1, 20), 
		}, 
		"bayes_opt": True, 
	}, 
}
