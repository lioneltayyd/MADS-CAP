import optuna 
import xgboost as xgb
from sklearn.linear_model import ElasticNet 



# -------------------------------------------------------
# General config 
# -------------------------------------------------------

# Directory path for saving and loading files or objects. 
DIR_DATASET = "dataset" 
DIR_DATASET_COLLECTION = f"{DIR_DATASET}/ner_collection" 
DIR_DATASET_LABELLINGS = f"{DIR_DATASET}/labelling" 
DIR_MLSPACY = "model/spacy_sentiment/v1" 
DIR_MLTOPIC = "model/topic_modelling" 
DIR_MLESTIM = "model/mktmv_estimator" 

# Define th starting and ending date when collecting the ticker data. 
TICKER_DATE_COLLECT = "1998-12-01", "2022-03-21" 

# Define the list of tickers we are interested to investigate on. 
TICKER_TO_COLLECT = ["SPY"] 

# Wikifier URL. 
WIKIFIER_URL = "http://www.wikifier.org/annotate-article"

# -------------------------------------------------------
# Define parameters 
# -------------------------------------------------------

PARAM_SEED = 42

# Wikifier parameters. 
PARAM_THRESHOLD = 0.8 
PARAM_LANG = "en" 

# Define the # of topics. 
PARAM_N_TOPIC = 8 
PARAM_TOP_N_TERM = 20 

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
