
import errno
import os
import glob
from enum import Enum
from pathlib import Path

from .json_builder import *
from .json_filler import *

class ConfigType(Enum):
    FILE = 1
    DIR = 2

class V2RAYConfigGenerator():
    def __init__(self, 
                input_path : str,
                output_path : str,
                config_type : ConfigType,
                structure : dict,
                setup_callback_func):
        """
        Initialize V2RAYConfigGenerator object.

        Args:
        input_path (str): path to the input config
        output_path (str): path to the output
        config_type (ConfigType): type of config
        structure (dict): a strcuture for building the json
        setup_callback_func (func): function for setting up callbacks
        """
        self._input_path = input_path
        self._output_path = output_path
        self._output_pathlib : Path = None
        self._config_type = config_type
        self._structure = structure
        self._setup_callback_func = setup_callback_func
        
    def _handle_json_dir(self):
        """
        Handle a dir of json files
        """
        jsb = JSONBuilder(self._input_path, self._structure)
        jsb.gather_all_files()
        jsb.build_json()
        self._output_pathlib.parent.mkdir(parents=True, exist_ok=True)
        self._output_pathlib.write_text(jsb.built_json)
        
        print(jsb.built_json)

    def _handle_json_file(self):
        """
        Handle a json files
        """
        with open(self._input_path, "r+") as f:
            jsf = JSONFiller(json.load(f))
            self._setup_callback_func(jsf)
            jsf.fill_json()
            self._output_pathlib.parent.mkdir(parents=True, exist_ok=True)
            json_out = json.dumps(jsf.filled_json, indent=2)
            self._output_pathlib.write_text(json_out)
        
            print(json_out)

    def build_configs(self):
        """
        Build V2Ray configs
        """
        if self._config_type == ConfigType.FILE:
            config_path = Path(self._input_path)
            self._output_pathlib = Path(self._output_path + "/" + config_path.name + ".json")
            if not config_path.exists():
                raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), self._input_path)
            if config_path.is_file():
                raise Exception("Specified json dir is not a folder")
            self._handle_json_dir()
            
        elif self._config_type == ConfigType.DIR:
            config_file = Path(self._input_path)
            self._output_pathlib = Path(self._output_path + "/" + config_file.name)
            if not config_file.exists():
                raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), self._input_path)
            if not config_file.is_file():
                raise Exception("Specified json dir is not a file")
            self._handle_json_file()
            

class EnvInjector():
    def __init__(self, input_path: str):
        """
        Constructor for the EnvInjector class.
        :param input_path: The path to the directory containing the .env files.
        """
        self._input_path = input_path
        self._injected_env = {}

    def inject_env(self):
        """
        Injects the environment variables from the .env files.
        """
        for env_file in glob.glob(f"{self._input_path}/*.env"):
            with open(env_file, "r+") as f:
                lines = f.readlines()
                for line in lines:
                    line = line.strip()  # Remove leading/trailing whitespace
                    if len(line) <= 2:  # Skip empty lines
                        continue
                    env_name, env_val = line.split("=")
                    os.environ[env_name] = env_val
                    self._injected_env[env_name] = env_val

    def remove_env(self):
        """
        Removes the environment variables that were injected.
        """
        for key in self._injected_env.keys():
            os.environ.pop(key)