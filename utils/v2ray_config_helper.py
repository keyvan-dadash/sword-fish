
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
        self._input_path = input_path
        self._output_path = output_path
        self._output_pathlib : Path = None
        self._config_type = config_type
        self._structure = structure
        self._setup_callback_func = setup_callback_func
        
    def _handle_json_dir(self):
        jsb = JSONBuilder(self._input_path, self._structure)
        jsb.gather_all_files()
        jsb.build_json()
        self._output_pathlib.parent.mkdir(parents=True, exist_ok=True)
        self._output_pathlib.write_text(jsb.built_json)
        
        print(jsb.built_json)

    def _handle_json_file(self):
        with open(self._input_path, "r+") as f:
            jsf = JSONFiller(json.load(f))
            self._setup_callback_func(jsf)
            jsf.fill_json()
            self._output_pathlib.parent.mkdir(parents=True, exist_ok=True)
            json_out = json.dumps(jsf.filled_json, indent=2)
            self._output_pathlib.write_text(json_out)
        
            print(json_out)

    def build_configs(self):
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
    
    def __init__(self, input_path : str):
        self._input_path = input_path
        self._injected_env = {}
        
    def inject_env(self):
        for env in glob.glob(f"{self._input_path}/*.env"):
            with open(env, "r+") as f:
                lines = f.readlines()
                for line in lines:
                    line = line.split("\n")[0]
                    if len(line) <= 2:
                        continue
                    env_name, env_val = line.split("=")
                    os.environ[env_name] = env_val
                    self._injected_env[env_name] = env_val
    
    def remove_env(self):
        for key in self._injected_env.keys():
            os.environ.pop(key)