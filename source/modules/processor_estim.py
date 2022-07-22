# %% 
# Python modules. 
import re, scipy, optuna 
import numpy as np 
import pandas as pd 
from typing import List, Dict, Any
import xgboost as xgb
from sklearn.linear_model import ElasticNet 
from sklearn.base import BaseEstimator, TransformerMixin 
from sklearn.utils.validation import check_is_fitted 
from feature_engine.encoding import OneHotEncoder 
from sklearn.model_selection import GridSearchCV 
from sklearn.pipeline import Pipeline 
from feature_engine.variable_manipulation import _check_input_parameter_variables 

# For clearing safe warnings. Not important. 
from IPython.display import clear_output 

# Custom configs. 
from source.config_py.config import PARAM_SEED, EXPERIMENT_COMPS, EXPERIMENT_MODEL 



# %%
class ColumnSelector(BaseEstimator, TransformerMixin):
    def __init__(self, var_proc): 
        self.var_proc = var_proc 
        self.feature_names_in_ = [] 
        self.feature_names_out = [] 

    def fit(self, X, y=None):
        # Track the input columns or features. 
        self.feature_names_in_ = X.columns.to_list() 
        return self 

    def transform(self, X): 
        X = X[self.var_proc] 
        # Track the output columns or features. 
        self.feature_names_out = X.columns.to_list() 
        return X 

    def get_feature_names_out(self) -> list: 
        # Check if the transformer has fitted or not before user can extract the output features. 
        check_is_fitted(self) 

        if self.feature_names_out: 
            return self.feature_names_out 

        print("No output features to display yet before transforming the features.") 



# %% 
def search_opt(
    estimator, 
    X, 
    y, 
    param_dist:dict, 
    cv:List,
    bayes:bool=True, 
    n_trials:int=50, 
    scoring:str="neg_root_mean_squared_error", 
    verbose:int=2
): 
    '''
    For hyperparameter tuning. Check out the following for guidance: 
    Bayesian: 
        - https://github.com/optuna/optuna-examples/blob/main/sklearn/sklearn_optuna_search_cv_simple.py 
        - https://www.section.io/engineering-education/optimizing-ml-models-with-optuna/ 
    ''' 
    # Setup the optimizer. 
    if bayes: 
        search_cv = optuna.integration.OptunaSearchCV(
            estimator, param_dist, cv=cv, n_trials=n_trials, 
            scoring=scoring, refit=True, timeout=600, verbose=verbose, 
            error_score="raise", random_state=PARAM_SEED, 
        ) 
    else: 
        search_cv = GridSearchCV(
            estimator, param_dist, cv=cv, scoring=scoring, 
            refit=True, verbose=verbose, 
        ) 
    
    # Run the optimization procedure. 
    search_cv.fit(X, y) 
    best_score = search_cv.study_.best_trial.value if bayes else search_cv.best_score_ 
    best_param = search_cv.study_.best_trial.params if bayes else search_cv.best_params_ 

    # Preview results. 
    print("-----" * 5) 
    print("Best trial") 
    print("-----" * 5) 
    print("Values       : ", best_score) 
    print("Params       : ")
    for k, v in best_param.items(): 
        print(f"\t {k}: {v}") 

    return search_cv 



# %% 
def multiverse_analysis(
    X:pd.DataFrame, 
    y:pd.DataFrame,
    cv:List,
    experiment_model:Dict[str,Any]=EXPERIMENT_MODEL,
    experiment_comps:Dict[str,Any]=EXPERIMENT_COMPS,
    n_trials:int=50, 
    verbose:int=2
) -> pd.DataFrame: 
    '''
    To perform multiverse analysis for various combination of components and models. 
    '''

    colnames = ["est_names", "estimator", "component", "rmse_avg", "rmse_std"]

    # To track the model performance for each combination of features and models. 
    df_performances = pd.DataFrame(columns=colnames) 

    # Explore the same set of componenets for each model choice. 
    for mlname, dict_mlparam in experiment_model.items(): 
        print(f"Performing search for ({mlname})") 

        # Experiment model training using different set of components. 
        for components in experiment_comps: 
            pipeline = [] 
            var_proc = [] 
            ohencode = [] 

            # Add the defined component to the pipeline. In the future, we can map the 
            # component name to the function using dictionary to dynamically obtain 
            # the function for specific component instead of hard code them this way. 
            for component, chosen_features in components.items(): 
                if component == "market_internal": 
                    var_proc.extend(chosen_features) 
                elif component == "valuation": 
                    var_proc.extend(chosen_features) 
                elif component == "eventflag": 
                    var_proc.extend(chosen_features) 
                elif component == "econometric": 
                    var_proc.extend(chosen_features) 
                elif component == "rp_sentiment": 
                    var_proc.extend(chosen_features) 
                elif component == "techind": 
                    var_proc.extend(chosen_features) 
                elif component == "candlestick": 
                    var_proc.extend(chosen_features) 

            # Transform categorical variable into OHE if any. 
            if ohencode: 
                pipeline.append(("oh_encoder", OneHotEncoder(drop_last=True, variables=ohencode))) 
        
            # Construct the pipeline. 
            mlpipe_estim = Pipeline([("select_col", ColumnSelector(var_proc=var_proc))] + pipeline) 
            X_trans = mlpipe_estim.fit_transform(X) 

            # Hyperparameter optimisation. 
            model, param = eval(dict_mlparam["model"]), eval(dict_mlparam["param_dist"]) 
            searchres = search_opt(
                model, X_trans, y, param, cv, dict_mlparam["bayes_opt"], n_trials, verbose=verbose
            ) 

            # Track the performance for various combination of components and model choice. 
            df_searchres = pd.DataFrame(columns=colnames) 
            df_searchres["est_names"] = [mlname] 
            df_searchres["estimator"] = [searchres.best_estimator_] 
            df_searchres["component"] = [str(components)] 
            df_searchres["ml_n_comp"] = [mlname + " + " + str(components)] 
            df_searchres["feat_name"] = [var_proc] 
            if dict_mlparam["bayes_opt"]: 
                df_searchres["rmse_avg"] = [searchres.study_.best_trial.user_attrs["mean_test_score"]] 
                df_searchres["rmse_std"] = [searchres.study_.best_trial.user_attrs["std_test_score"]] 
            else: 
                df_searchres["rmse_avg"] = [searchres.cv_results_["mean_test_score"][searchres.best_index_]] 
                df_searchres["rmse_std"] = [searchres.cv_results_["std_test_score"][searchres.best_index_]] 

            # Consolidate the performance result. 
            df_performances = pd.concat([df_performances, df_searchres], axis="index") 

            # Clear safe warnings. Not important. 
            clear_output() 

    return df_performances 
