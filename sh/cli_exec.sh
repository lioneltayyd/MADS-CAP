# # Run this to download SpaCy pipeline for the older version. 
python -m spacy download en 

# Run this to download SpaCy pipeline for the latest version. 
python -m spacy download en_core_web_sm

# Run this to download SpaCy transformer pipeline. 
python -m spacy download en_core_web_trf

# Autofill the SpaCy config. 
python -m spacy init fill-config config/base_config.cfg config/config.cfg 

# Train sentiment model via SpaCy. 
python -m spacy train source/config_spacy/config_tp.cfg \
	--verbose  \
	--output model/spacy_sentiment 

# Train sentiment model via SpaCy with Transformers. 
python -m spacy train source/config_spacy/config_dl.cfg \
	--verbose  \
	--gpu-id 0 \
	--output model/spacy_sentiment 
