# %%
# Python modules. 
import os, time, urllib, json, re 
import spacy 
import numpy as np 
import pandas as pd
from collections import defaultdict 
from sklearn.metrics.pairwise import cosine_similarity 

# Custom configs. 
from source.config_py.config import (
    WIKIFIER_URL, PARAM_THRESHOLD, PARAM_LANG, 
    PARAM_N_TOPIC, PARAM_TOP_N_TERM 
)



# %%
def resolve_coref(text:str, nlp:spacy.tokens.doc.Doc): 
    '''Identify the co-referencing part for the body text and replace them.'''

    doc = nlp(text)

    # Get the tokens including whitespaces from (spacy doc object). 
    tokens = list(token.text_with_ws for token in doc)

    for cluster in doc._.coref_clusters:
        # Get tokens from representative cluster name. 
        cluster_main_words = set(cluster.main.text.split(' '))

        for coref in cluster:
            # If coreference element is not the representative element of that cluster do the following. 
            if coref != cluster.main: 
                if coref.text != cluster.main.text and bool(set(coref.text.split(' ')).intersection(cluster_main_words)) == False:
                    # If coreference element text and representative element text are not equal 
                    # and none of the coreference element words are in representative element, 
                    # do this to handle nested coreference scenarios. 
                    tokens[coref.start] = cluster.main.text + doc[coref.end-1].whitespace_ 
                    for i in range(coref.start+1, coref.end): 
                        tokens[i] = "" 

    return "".join(tokens)



# %%
def wikifier_extract(text:str, lang:str=PARAM_LANG, threshold:int=PARAM_THRESHOLD) -> dict: 
    '''
    Get the entities and POS from Wikifier API. Link to the UI page for documentation and testing: 
    - https://wikifier.org/info.html#wikification 
    - https://wikifier.org/ 
    ''' 
    
    # URL parameter setup. 
    data = urllib.parse.urlencode([
        ("text", text), 
        ("lang", lang),
        ("userKey", os.environ["WIKIFIER_USERKEY"]), 
        ("pageRankSqThreshold", str(threshold)), 
        ("applyPageRankSqThreshold", "true"), 
        ("nTopDfValuesToIgnore", "100"), 
        ("nWordsToIgnoreFromList", "100"),
        ("wikiDataClasses", "true"), 
        ("wikiDataClassIds", "false"),
        ("support", "true"), 
        ("ranges", "false"), 
        ("minLinkFrequency", "2"),
        ("includeCosines", "false"), 
        ("maxMentionEntropy", "3"), 
        ("partsOfSpeech", "true"), 
    ])

    # Receive the POST response from Wikifier. 
    request = urllib.request.Request(WIKIFIER_URL, data=data.encode("utf8"), method="POST") 
    with urllib.request.urlopen(request, timeout=60) as f: 
        response = f.read() 
        response = json.loads(response.decode("utf8")) 

    # Sleep for a while to avoid rate limit issue. 
    time.sleep(2) 

    # Need to convert the (collections.defaultdict) object to normal (dict) object 
    # later, so that we can save the object in (Parquet) format. 
    ent_results = defaultdict(lambda: []) 
    pos_results = dict() 

    # Wikifier sometimes may not be able to extract entities and POS tags due to 
    # error like: 
    #   >> Input text is too long (30180 characters, max allowed = 25000). 
    #   >> Response does not contain (wikiDataClasses). 
    # You can identify which headline ID does the error occurs at and debug 
    # from there by searching for empty (dict) object. 
    try: 
        # Extract the POS tags. 
        pos_results = {
            "verbs"        : [postag["normForm"] for postag in response["verbs"]], 
            "nouns"        : [postag["normForm"] for postag in response["nouns"]], 
            "adjectives"   : [postag["normForm"] for postag in response["adjectives"]], 
            "adverbs"      : [postag["normForm"] for postag in response["adverbs"]], 
        } 
        
        # Extract the entities for specific news article. 
        for annotation in response["annotations"]: 
            if "wikiDataClasses" in annotation: 
                ent_results["title"].append(annotation["title"])
                ent_results["wikiId"].append(annotation["wikiDataItemId"])
                ent_results["dblabel"].append([dblabel for dblabel in annotation["dbPediaTypes"]])
                ent_results["enlabel"].append([enlabel["enLabel"] for enlabel in annotation["wikiDataClasses"]])
                ent_results["characters"].append([(enlabel["chFrom"], enlabel["chTo"]) for enlabel in annotation["support"]]) 
    except: 
        return {"entities": dict(ent_results), "pos_tags": pos_results} 

    return {"entities": dict(ent_results), "pos_tags": pos_results} 



# %%
def raw_token_input(tokens:list) -> list: 
	'''
    Redefine the tokenization process. Basically remove the Sklearn's 
    default preprocessing steps and only return the list of tokens since 
    we have extracted the tokens (entities) and placed them in a list. 
    The output should contain multiple list of tokens (entities). 
    ''' 
	return tokens 



# %%
def get_topic_similarity(component:np.array) -> pd.DataFrame: 
    '''Get cosine similarity score between each pair of topics.''' 
    # Topic names. 
    topic_names = [f"TP{topic_i}" for topic_i in range(0, PARAM_N_TOPIC)] 

    # Compute cosine similarity score. 
    df_topic_sim = pd.DataFrame(cosine_similarity(component), columns=topic_names) 
    df_topic_sim["topic"] = topic_names 

    # Convert into long table. 
    df_topic_sim = df_topic_sim.melt(
        id_vars="topic", value_vars=topic_names, var_name="to_compare", value_name="topic_similarity"
    ) 

    return df_topic_sim 



# %%
def get_token_weight(component:np.array, feature_names:np.array) -> pd.DataFrame: 
    '''Get token weights for each token name for each topic.''' 

    topic_key_tokens = defaultdict(lambda: {}) 

    # # To store the coherance scores.
    # coherence_scores = [] 

    # Topic names. 
    topic_names = [f"TP{topic_i}" for topic_i in range(0, PARAM_N_TOPIC)] 

    # Evaluate the topic clustering outcome. 
    for topic_index in range(0, PARAM_N_TOPIC): 
        # Find the top N terms for each topic. 
        top_indices = np.argsort(component[topic_index, :])[::-1] 

        # Token names that are related to specific topic. 
        topic_terms = [feature_names[term_index] for term_index in top_indices[:PARAM_TOP_N_TERM]] 
        topic_key_tokens[topic_index]["topic_terms"] = topic_terms 

        # Token weight related to specific topic. 
        token_weight = [component[topic_index, term_index] for term_index in top_indices[:PARAM_TOP_N_TERM]] 
        topic_key_tokens[topic_index]["token_weight"] = token_weight 

        # # Compute the coherence score. Need to use embeddings. 
        # coherence_scores.append(topical_coherence(topic_terms)) 

    df_token_weight = pd.DataFrame(topic_key_tokens).T 
    df_token_weight["topic"] = topic_names 
    df_token_weight = df_token_weight.explode(column=["topic_terms", "token_weight"]) 

    return df_token_weight 



# %% 
def get_center_component(headline_id:np.array, latent_feature:np.array) -> pd.DataFrame: 
    '''Get the center value of the component for each topic.''' 

    # Topic names. 
    topic_names = [f"TP{topic_i}" for topic_i in range(0, PARAM_N_TOPIC)] 

    # Get the topic cluster label. 
    latent_topic = np.argmax(latent_feature, axis=1) 

    # Reorganise the data in dataframe. 
    df_latent_feature = pd.DataFrame(data=latent_feature, columns=topic_names) 
    df_center_component = pd.DataFrame(data={"headline_id": headline_id, "topic": latent_topic}) 
    df_center_component = pd \
        .concat([df_center_component, df_latent_feature], axis="columns") \
        .loc[:,"topic":].groupby("topic").mean() 

    return df_center_component 



# %% 
def get_token_variation(row:pd.Series) -> list: 
	'''Get every possible unique variation of strings from each extracted entity title.''' 

	token_variation = [] 
	ent_title = row["entities"]["title"] 
	ent_chars = row["entities"]["characters"] 
	body_text = row["article_text"] 

    # Assign nothing if no entities title is found for specific articles. 
    # This can happen because Wifikier API error such as: 
    #   >> Input text is too long (30180 characters, max allowed = 25000). 
    #   >> Response does not contain (wikiDataClasses). 
	if isinstance(ent_title, type(None)): 
		return None 

	for i, _ in enumerate(ent_title): 
		# To store unique strings to be replaced. 
		span_token = set() 

		# Get every possible unique variation of strings for replacement later. 
		for span in ent_chars[i]: 
			# Extract the text. 
			span_beg, span_end = tuple(span) 
			text = body_text[span_beg:span_end+1] 

			# Replace non-word and non-whitespace string. 
			text = re.sub(r"[^\w\s]*", "", text).strip() 
			
			# In case of empty string, ignore it. 
			if text: 
				span_token.add(text) 
	
		# To track each unique set of strings for each entity title. 
		token_variation.append(span_token) 
	return token_variation 



# %% 
def replace_references(row:pd.Series) -> str: 
	'''Replace specific text with entities title.''' 
	
	ent_title = row["entities"]["title"] 
	token_variation = row["token_variation"] 
	body_text = row["article_text"] 

    # Assign nothing if no text (ones to be replaced) is found for specific articles. 
    # This can happen because Wifikier API error such as: 
    #   >> Input text is too long (30180 characters, max allowed = 25000). 
    #   >> Response does not contain (wikiDataClasses). 
	if isinstance(token_variation, type(None)): 
		return None 

	for i, span_token in enumerate(token_variation): 
		# Replace strings with the given entity title. 
		for to_be_replaced in span_token: 
			title_phrase = ent_title[i].strip().replace(" ", "_") 
			body_text = re.sub(f"\\b{to_be_replaced}\\b", title_phrase, body_text) 

			print(to_be_replaced, " >> ", title_phrase) 
		print("-----" * 5) 
	return body_text 
