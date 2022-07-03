# %%
# Python modules. 
import os, re, pickle 
import pandas as pd
import spacy 
from spacy.tokens import DocBin 

# Custom configuration.
from source.config_py.config import DIR_DATASET



# %%
class ManageFiles():
	def __init__(self, dataset_dir:str=DIR_DATASET):
		'''General files class with common methods needed for all files.'''

		self.dataset_dir = dataset_dir 


	def write_to_csv(self, data:pd.DataFrame, filename:str=None, **kwargs):
		'''Write dataframe to csv file.'''

		print(f"Write to ({filename})") 

		# Check directories. 
		self._get_ready_for_file_operation()

		# Write files. 
		filepath = os.path.join(self.dataset_dir, filename) 
		data.to_csv(filepath, **kwargs) 


	def read_from_csv(self, filename:str=None, **kwargs):
		'''Read csv file into dataframe.'''

		print(f"Read from ({filename})") 

		# Check directories. 
		self._get_ready_for_file_operation()

		# Read files. 
		filepath = os.path.join(self.dataset_dir, filename) 
		df = pd.read_csv(filepath, **kwargs) 
		return df


	def write_to_parquet(self, data:pd.DataFrame, filename:str=None, **kwargs):
		'''Write dataframe to parquet file.'''

		print(f"Write to ({filename})") 

		# Check directories. 
		self._get_ready_for_file_operation()

		# Write files. 
		filepath = os.path.join(self.dataset_dir, filename) 
		data.to_parquet(filepath, **kwargs) 


	def read_from_parquet(self, filename:str=None, **kwargs):
		'''Read parquet file into dataframe.'''

		print(f"Read from ({filename})") 

		# Check directories. 
		self._get_ready_for_file_operation()

		# Read files. 
		filepath = os.path.join(self.dataset_dir, filename) 
		df = pd.read_parquet(filepath, **kwargs) 
		return df


	def save_cache_pk(self, dir:str=None, filename:str=None, object=None): 
		'''Cache the result.''' 

		print(f"Save to ({filename})") 

		# Check directories. 
		self._get_ready_for_file_operation()

		path = os.path.join(dir, filename) 
		with open(path, "wb") as f: 
			pickle.dump(object, f) 


	def load_cache_pk(self, dir:str=None, filename:str=None): 
		'''Load the cache.''' 

		print(f"Load from ({filename})") 

		# Check directories. 
		self._get_ready_for_file_operation()

		path = os.path.join(dir, filename) 
		with open(path, "rb") as f: 
			return pickle.load(f) 


	def save_version_pk(self, dir:str=None, obj_name:str=None, object=None, dev_status:bool=True): 
		'''Save the object and assign the version.''' 

		print(f"Save object ({obj_name}).") 

		# Check directories. 
		self._get_ready_for_file_operation() 

		# Load the current version and get the dev folder. 
		dev_status, version = self.resume_version(dir, dev_status=dev_status) 
		obj_name = f"{obj_name}_v{version}.pickle" 

		# Save the model. 
		path = os.path.join(dir, dev_status, obj_name) 
		with open(path, "wb") as f: 
			pickle.dump(object, f) 

		# Increment the version by 1 after saving it. 
		self.update_version(dir, version, dev_status=True) 


	def load_version_pk(self, dir:str=None, obj_name:str=None, version_load:str="latest", dev_status:bool=True): 
		'''Load the object with specific version.''' 

		print(f"Load object ({obj_name}).") 

		# Check directories. 
		self._get_ready_for_file_operation() 

		# Load the model specific version and get the dev folder. 
		dev_status, version = self.resume_version(dir, dev_status=dev_status) 
		version_load = str(version) if version_load == "latest" else version_load 
		obj_name = f"{obj_name}_v{int(version) - 1}.pickle" 

		# Load the model. 
		path = os.path.join(dir, dev_status, obj_name) 
		with open(path, "rb") as f: 
			return pickle.load(f) 


	def save_to_spacy(self, data:spacy.tokens.doc.Doc, filename:str, nlp:spacy.tokens.doc.Doc): 
		'''Save dataset in SpaCy format.'''
		
		print(f"Save to ({filename})") 

		path = os.path.join(self.dataset_dir, filename) 
		doc_bin = DocBin(docs=to_spacy_document(nlp, data)) 
		doc_bin.to_disk(path) 


	def update_version(self, dir:str=None, version:int=None, dev_status:bool=True): 
		'''For versioning.''' 

		# Check directories. 
		self._get_ready_for_file_operation() 
		
		dev_status = "dev" if dev_status else "prod" 
		path = os.path.join(dir, dev_status, "VERSION") 
		with open(path, "w") as f: 
			version += 1 
			print(f"Updated version: ({version}) in ({dev_status})") 
			f.write(str(version)) 


	def resume_version(self, dir:str=None, dev_status:bool=True): 
		'''Resume the latest version.''' 

		# Ensure the directories and version file exists. 
		self._confirm_version_exist(dir, dev_status) 

		dev_status = "dev" if dev_status else "prod" 
		path = os.path.join(dir, dev_status, "VERSION") 
		with open(path, "r") as f: 
			dev_status, version = dev_status, int(f.read()) 
			print(f"Resumed version: ({version}) from ({dev_status})") 
			return dev_status, version 


	def _get_ready_for_file_operation(self):
		'''Handles the necessary checks prior to any file operation.'''

		self._confirm_current_working_directory()
		self._confirm_dataset_directory() 


	def _confirm_current_working_directory(self):
		'''Set working directory to project directory.'''

		if not re.match(r".+/MADS-M2-estimating-news-impact-on-financial-market$", os.getcwd()): 
			os.chdir("../..") 


	def _confirm_dataset_directory(self):
		'''Checks for existince of dataset directory and creates if needed.'''

		if not os.path.exists(self.dataset_dir):
			os.makedirs(self.dataset_dir) 


	def _confirm_version_exist(self, dir:str, dev_status:bool=True): 
		'''Checks for existince of directories and version and initiate them if needed.''' 

		dev_status = "dev" if dev_status else "prod" 
		path = os.path.join(dir, dev_status) 

		# Create the directory. 
		if not os.path.exists(path): 
			os.makedirs(path) 

			# Create the version file. 
			with open(os.path.join((path, "VERSION")), "x") as f: 
				version = 1 
				f.write(str(version)) 



# %%
def to_spacy_document(nlp:spacy.tokens.doc.Doc, data:tuple) -> spacy.tokens.doc.Doc: 
	'''
	Convert the TRAIN and TEST into SpaCy document. For more information on
	how to enable and disable SpaCy pipeline check out the following links: 
	- https://spacy.io/api/language#pipe 
	- https://spacy.io/usage/processing-pipelines
	- https://spacy.io/usage/processing-pipelines#disabling
	'''
	print("Reformatting the dataset...") 

	# To store a list of (Spacy Doc) object. 
	text = []

	# Use SpaCy Doc object to categorise the sentiment. 
	for doc, label in nlp.pipe(data, as_tuples=True): 
		if label =="positive":
			doc.cats["positive"] = 1
			doc.cats["negative"] = 0
			doc.cats["neutral"]  = 0
		elif label == "negative":
			doc.cats["positive"] = 0
			doc.cats["negative"] = 1
			doc.cats["neutral"]  = 0
		else:
			doc.cats["positive"] = 0
			doc.cats["negative"] = 0
			doc.cats["neutral"]  = 1
		text.append(doc) 

	print("Reformatted the dataset.") 

	return text 
