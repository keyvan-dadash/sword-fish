import glob
import json
from collections import OrderedDict
from .json_filler import JSONFiller

class JSONBuilder():
    
    def __init__(self, config_folder_path : str, json_structure : list) -> None:
        self._config_folder = config_folder_path
        self._files = {}
        self._json_structure = json_structure
        
        
    def gather_all_files(self):
        for json_config in glob.glob(f"{self._config_folder}/*.json"):
            file_type = json_config.split("/")[-1].split(".")[0]
            self._files[file_type] = json_config
            
    def build_json(self):
        built_json = OrderedDict()
        for structure_name, setup_callback in self._json_structure:
            json_config = self._files[structure_name]
            with open(json_config, 'r+') as config_f:
                json_config = json.load(config_f)
                json_filler = JSONFiller(json_config)
                setup_callback(json_filler)
                json_filler.fill_json()
                built_json[structure_name] = json_filler.filled_json
        self._built_json = json.dumps(built_json, indent=2)
        
    @property
    def built_json(self):
        return self._built_json