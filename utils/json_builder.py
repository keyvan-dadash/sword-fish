import glob
import json
from collections import OrderedDict
from .json_filler import JSONFiller


class JSONBuilder():
    def __init__(self, config_folder_path: str, json_structure: list) -> None:
        """
        Initialize JSONBuilder object

        Args:
        config_folder_path (str): path to the config folder which contains various json files
        json_structure (list): the structure which provide in which order json files should assemble
        """
        self._config_folder = config_folder_path
        self._files = {}
        self._json_structure = json_structure
        
    def gather_all_files(self):
        """
        Find and gather all json files
        """
        for json_config in glob.glob(f"{self._config_folder}/*.json"):
            # Extract the file name from the file path.
            file_type = json_config.split("/")[-1].split(".")[0]
            # Add the file to the _files dictionary with the file name as the key and file path as the value.
            self._files[file_type] = json_config
            
    def build_json(self):
        """
        Start to build json files
        """
        # Build the JSON structure using the saved JSON files and JSONFiller.
        built_json = OrderedDict()
        for structure_name, setup_callback in self._json_structure:
            # Get the JSON configuration file path from _files dictionary.
            json_config = self._files[structure_name]
            with open(json_config, 'r+') as config_f:
                # Load JSON from the configuration file.
                json_config = json.load(config_f)
                # Create a JSONFiller object and pass in the JSON configuration.
                json_filler = JSONFiller(json_config)
                # Call the provided setup callback function to set up the JSONFiller.
                setup_callback(json_filler)
                # Fill the JSON configuration with environment variables and convert it to a string.
                json_filler.fill_json()
                # Add the filled JSON to the built_json dictionary.
                built_json[structure_name] = json_filler.filled_json
        # Convert the built_json dictionary to a string and save it in the _built_json attribute.
        self._built_json = json.dumps(built_json, indent=2)
        
    @property
    def built_json(self):
        """
        Get built json
        
        Returns:
        str: return built json
        """
        # Return the _built_json attribute.
        return self._built_json