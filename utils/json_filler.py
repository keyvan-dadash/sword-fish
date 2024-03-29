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
        """
        Initialize JSONFiller object with a JSON configuration.

        Args:
        json_config (str): a JSON configuration string
        """
        self._json_config = json_config
        self._dict_callback = lambda x : x
        self._list_callback = lambda x : x
        self._str_callback = lambda x : x
        self._val_callback = lambda x, y : x
        self._end_process = lambda x, y : x
        self._eligible_val = lambda x : x

    def fill_json(self):
        """
        Fill in environment variables in the JSON configuration.

        Returns:
        str: a string of the JSON configuration with the environment variables filled in
        """
        self._substitude_env_vars(self._json_config)
        return self._json_config
    
    def set_callback_on_dict(self, callback):
        """
        Set the callback function for processing a dictionary.

        Args:
        callback: the callback function
        """
        self._dict_callback = callback
        
    def set_callback_on_list(self, callback):
        """
        Set the callback function for processing a list.

        Args:
        callback: the callback function
        """
        self._list_callback = callback
        
    def set_callback_on_str(self, callback):
        """
        Set the callback function for processing a string.

        Args:
        callback: the callback function
        """
        self._str_callback = callback
        
    def set_callback_on_val(self, callback):
        """
        Set the callback function for processing a value.

        Args:
        callback: the callback function
        """
        self._val_callback = callback
        
    def set_callback_end_of_process(self, callback):
        """
        Set the callback function for the end of processing.

        Args:
        callback: the callback function
        """
        self._end_process = callback
        
    def set_callback_eligible(self, callback):
        """
        Set the callback function for eligibility.

        Args:
        callback: the callback function
        """
        self._eligible_val = callback
    
    @property
    def filled_json(self):
        """
        Get the JSON configuration string with environment variables filled in.

        Returns:
        str: the JSON configuration string with environment variables filled in
        """
        return self._json_config
        
    def _process_str(self, v):
        """
        Process a string with an environment variable.

        Args:
        v (str): a string containing an environment variable

        Returns:
        str or int: the processed string or integer
        """
        m = re.match('(.*?)\${(\w+)\:-(\w+)}(.*)', v)
        if m:
            env_name = m.group(2)
            def_val = m.group(3)
            env_val = os.environ.get(env_name)
            if env_val is None:
                env_val = cast_to_type(def_val)
            
            if self._eligible_val(env_name): # if variable is eligiable for calling callback
                env_val = self._val_callback(env_name, env_val)
            result = m.group(1) + env_val + m.group(4)
            result_without_qut = result.replace("\"", "")
            try:
                result = int(result_without_qut)
            except:
                pass
            return result
        return v

    def _process_list(self, v):
        """
        Process a list with an environment variable in recursive order.

        Args:
        v (list): a list containing an environment variable

        Returns:
        list: processed list
        """
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
        """
        Process a given input with an environment variable in recursive order.

        Args:
        d (variable): a object(list or dirct) to be processed
        """
        if isinstance(d, list):
            self._list_callback(d)
            self._process_list(d)
            self._end_process(d, ProcessedType.LIST)
        else:
            tmp = {}
            for key in d.keys():
                new_key = self._process_str(key)
                v = d.get(key)
                new_val = v
                if isinstance(v, str):
                    self._str_callback(v)
                    new_val = self._process_str(v)
                    d[key] = new_val
                    self._end_process(new_val, ProcessedType.STR)
                elif isinstance(v, list):
                    self._list_callback(v)
                    new_val = self._process_list(v)
                    d[key] = new_val
                    self._end_process(new_val, ProcessedType.LIST)
                elif isinstance(v, dict):
                    self._dict_callback(v)
                    self._substitude_env_vars(v)
                    new_val = v
                    self._end_process(new_val, ProcessedType.DICT)

                if key != new_key:
                    tmp[new_key] = (key, new_val)
            
            for key, value in tmp.items():
                d[key] = value[1]
                d.pop(value[0])