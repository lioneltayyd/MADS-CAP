# %%
# Python modules. 
import os, re, pickle 
import pandas as pd

# Custom configuration.
from source.config_py.config import DIR_ROOT, DIR_DATASET, DIR_MLMODEL 



# %%
class ManageFiles():
	def __init__(self, dataset_dir:str=DIR_DATASET, mlmodel_dir:str=DIR_MLMODEL): 
		'''General files class with common methods needed for all files.'''

		self.dataset_dir = dataset_dir 
		self.mlmodel_dir = mlmodel_dir 


	def pd_write_to(self, data:pd.DataFrame, dirpath:str, filename:str, format="csv", **kwargs):
		'''Write dataframe.'''

		print(f"Write to ({filename})") 

		# Check directories. 
		self._get_ready_for_file_operation(dirpath) 

		# Write files. 
		filepath = os.path.join(dirpath, filename) 

		if format == "csv": 
			data.to_csv(filepath, index=False, **kwargs) 
		elif format == "parquet": 
			data.to_parquet(filepath, index=False, **kwargs) 


	def pd_read_from(self, dirpath:str, filename:str, format="csv", **kwargs) -> pd.DataFrame:
		'''Read into dataframe.'''

		print(f"Read from ({filename})") 

		# Check directories. 
		self._get_ready_for_file_operation(dirpath) 

		# Read files. 
		filepath = os.path.join(dirpath, filename) 

		if format == "csv": 
			df = pd.read_csv(filepath, **kwargs) 
		elif format == "parquet": 
			df = pd.read_parquet(filepath,  **kwargs) 

		return df 


	def save_cache_pk(self, dirpath:str=None, filename:str=None, object=None): 
		'''Cache the result.''' 

		print(f"Save to ({filename})") 

		# Check directories. 
		self._get_ready_for_file_operation(dirpath)

		filepath = os.path.join(dirpath, filename) 
		with open(filepath, "wb") as f: 
			pickle.dump(object, f) 


	def load_cache_pk(self, dirpath:str=None, filename:str=None): 
		'''Load the cache.''' 

		print(f"Load from ({filename})") 

		# Check directories. 
		self._get_ready_for_file_operation(dirpath)

		filepath = os.path.join(dirpath, filename) 
		with open(filepath, "rb") as f: 
			return pickle.load(f) 


	def save_version_pk(self, dirpath:str=None, obj_name:str=None, object=None, dev_status:bool=True): 
		'''Save the object and assign the version.''' 

		print(f"Save object ({obj_name}).") 

		# Check directories. 
		self._get_ready_for_file_operation(dirpath) 

		# Load the current version and get the dev folder. 
		dev_status, version = self.resume_version(dirpath, dev_status=dev_status) 
		obj_name = f"{obj_name}_v{version}.pickle" 

		# Save the model. 
		filepath = os.path.join(dirpath, dev_status, obj_name) 
		with open(filepath, "wb") as f: 
			pickle.dump(object, f) 

		# Increment the version by 1 after saving it. 
		self.update_version(dirpath, version, dev_status=True) 


	def load_version_pk(self, dirpath:str=None, obj_name:str=None, version_load:str="latest", dev_status:bool=True): 
		'''Load the object with specific version.''' 

		print(f"Load object ({obj_name}).") 

		# Check directories. 
		self._get_ready_for_file_operation(dirpath) 

		# Load the model specific version and get the dev folder. 
		dev_status, version = self.resume_version(dirpath, dev_status=dev_status) 
		version_load = str(version) if version_load == "latest" else version_load 
		obj_name = f"{obj_name}_v{int(version) - 1}.pickle" 

		# Load the model. 
		filepath = os.path.join(dirpath, dev_status, obj_name) 
		with open(filepath, "rb") as f: 
			return pickle.load(f) 


	def update_version(self, dirpath:str=None, version:int=None, dev_status:bool=True): 
		'''For versioning.''' 

		# Check directories. 
		self._get_ready_for_file_operation(dirpath) 
		
		dev_status = "dev" if dev_status else "prod" 
		filepath = os.path.join(dirpath, dev_status, "VERSION") 
		with open(filepath, "w") as f: 
			version += 1 
			print(f"Updated version: ({version}) in ({dev_status})") 
			f.write(str(version)) 


	def resume_version(self, dirpath:str=None, dev_status:bool=True): 
		'''Resume the latest version.''' 

		# Ensure the directories and version file exists. 
		self._confirm_version_exist(dirpath, dev_status) 

		dev_status = "dev" if dev_status else "prod" 
		filepath = os.path.join(dirpath, dev_status, "VERSION") 
		with open(filepath, "r") as f: 
			dev_status, version = dev_status, int(f.read()) 
			print(f"Resumed version: ({version}) from ({dev_status})") 
			return dev_status, version 


	def _get_ready_for_file_operation(self, dirpath:str):
		'''Handles the necessary checks prior to any file operation.'''

		self._confirm_current_working_directory()
		self._confirm_dataset_directory(dirpath) 


	def _confirm_current_working_directory(self):
		'''Set working directory to project or root directory.'''

		while not re.match(f".+{DIR_ROOT}$", os.getcwd()): 
			os.chdir("..") 


	def _confirm_dataset_directory(self, dirpath:str):
		'''Checks for existince of dataset directory and creates if needed.'''

		os.makedirs(self.dataset_dir, exist_ok=True) 
		os.makedirs(self.mlmodel_dir, exist_ok=True) 
		os.makedirs(dirpath, exist_ok=True) 


	def _confirm_version_exist(self, dirpath:str, dev_status:bool=True): 
		'''Checks for existince of directories and version and initiate them if needed.''' 

		dev_status = "dev" if dev_status else "prod" 
		path = os.path.join(dirpath, dev_status) 

		# Create the directory. 
		if not os.path.exists(path): 
			os.makedirs(path) 

			# Create the version file. 
			with open(os.path.join((path, "VERSION")), "x") as f: 
				version = 1 
				f.write(str(version)) 
