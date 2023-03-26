import os
import re
from enum import Enum
from .cast import *

class ProcessedType(Enum):
    STR = 1
    LIST = 2
    DICT = 3

class JSONFiller():
    def __init__(self, json_config : str) -> None:
        self._json_config = json_config
        self._dict_callback = lambda x : x
        self._list_callback = lambda x : x
        self._str_callback = lambda x : x
        self._val_callback = lambda x : x
        self._end_process = lambda x, y : x
        
    def fill_json(self):
        self._substitude_env_vars(self._json_config)
        return self._json_config
    
    def set_callback_on_dict(self, callback):
        self._dict_callback = callback
        
    def set_callback_on_list(self, callback):
        self._list_callback = callback
        
    def set_callback_on_str(self, callback):
        self._str_callback = callback
        
    def set_callback_on_val(self, callback):
        self._val_callback = callback
        
    def set_callback_end_of_process(self, callback):
        self._end_process = callback
        
    def set_callback_eligible(self, callback):
        self._eligible_val = callback
    
    @property
    def filled_json(self):
        return self._json_config
        
    def _process_str(self, v):
        m = re.match('(.*?)\${(\w+)\:-(\w+)}(.*)', v)
        if m:
            env_name = m.group(2)
            def_val = m.group(3)
            env_val = os.environ.get(env_name)
            if env_val is None:
                env_val = cast_to_type(def_val)
            
            if self._eligible_val(env_name):
                env_val = self._val_callback(env_val)
            result = m.group(1) + env_val + m.group(4)
            result_without_qut = result.replace("\"", "")
            try:
                result = int(result_without_qut)
            except:
                pass
            return result
        return v

    def _process_list(self, v):
        for index, item in enumerate(v):
            if isinstance(item, dict):
                self._dict_callback(item)
                self._substitude_env_vars(item)
                self._end_process(item, ProcessedType.DICT)
            elif isinstance(item, list):
                self._list_callback(item)
                v[index] = self._process_list(item)
                self._end_process(item, ProcessedType.LIST)
            elif isinstance(item, str):
                self._str_callback(item)
                v[index] = self._process_str(item)
                self._end_process(item, ProcessedType.STR)
        return v

    def _substitude_env_vars(self, d):
        if isinstance(d, list):
            self._list_callback(d)
            self._process_list(d)
            self._end_process(d, ProcessedType.LIST)
        else:
            for key in d.keys():
                v = d.get(key)
                if isinstance(v, str):
                    self._str_callback(v)
                    d[key] = self._process_str(v)
                    self._end_process(v, ProcessedType.STR)
                elif isinstance(v, list):
                    self._list_callback(v)
                    d[key] = self._process_list(v)
                    self._end_process(v, ProcessedType.LIST)
                elif isinstance(v, dict):
                    self._dict_callback(v)
                    self._substitude_env_vars(v)
                    self._end_process(v, ProcessedType.DICT)