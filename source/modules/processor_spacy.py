# %%
# Python modules. 
import spacy 

# Custom configs. 
from source.config_py.config import DIR_MLSPACY 



# %%
# Loading the best model. 
mlpipe_spacy = spacy.load(f"{DIR_MLSPACY}/model-best") 
tokenz_spacy = spacy.tokenizer.Tokenizer(mlpipe_spacy.vocab) 



# %%
def sentiment_predictor(texts): 
    '''
    To make prediction via SpaCy model, so that SHAP can evaluate the model. 
    '''
    mlpipe_class = list(mlpipe_spacy.get_pipe("textcat").labels) 

    # Convert texts to bare strings. 
    texts = [str(text) for text in texts] 
    results = []
    
    # Predict the sentitment. 
    for doc in mlpipe_spacy.pipe(texts): 
        results.append([doc.cats[cat] for cat in mlpipe_class]) 
    return results



# %%
def token_wrapper(text, return_offsets_mapping=False):
    '''
    A function to create a transformers-like tokenizer to match shap's expectations.
    We are taking the normalized tokens by default. Check this out for reference on
    normalization: 
        - https://newscatcherapi.com/blog/spacy-vs-nltk-text-normalization-comparison-with-code-examples 
    '''

    # Split text into tokens. 
    doc = tokenz_spacy(text) 

    # Extract the normalized token. 
    # Check this: 
    out = {"input_ids": [tok.norm for tok in doc]}

    # Take the span of a token. 
    if return_offsets_mapping:
        out["offset_mapping"] = [(tok.idx, tok.idx + len(tok)) for tok in doc] 
    return out
