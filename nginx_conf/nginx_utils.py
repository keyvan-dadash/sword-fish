#!/usr/bin/python3

import json

if __name__ == '__main__':
    from nginx_fmt import Formatter
    from . import nginx_config_helper as nginx
else:
    from .nginx_fmt import Formatter
    from . import nginx_config_helper as nginx
    
    
class NGINXParser():
    def __init__(self, nginx_config_path : str):
        """
        Initialize NGINXParser object.

        Args:
        nginx_config_path (str): path to the nginx config
        """
        self._config_path = nginx_config_path
        self._extracted_config : nginx.Conf = None
    
    def extract_config(self):
        """
        Extract configs to a nginx.Conf
        """
        self._extracted_config = nginx.loadf(self._config_path)
        
    @property
    def as_json(self):
        """
        Get json of nginx conf
        
        Returns:
        str: json of extracted configs
        """
        return json.dumps(self._extracted_config.as_dict, indent=2)
        
    @property
    def as_dict(self):
        """
        Get dict of nginx conf
        
        Returns:
        dict: dict of extracted configs
        """
        return self._extracted_config.as_dict

class NGINXConfigBlockBuilder():
    def __init__(self, block_dict : dict):
        """
        Initialize NGINXConfigBlockBuilder object.

        Args:
        block_dict (dict): dict of nginx conf
        """
        self._nginx_formatted_conf = ""
        self._block_dict = block_dict
        self._formatter = Formatter()
    
    def generate_formatted_nginx_config(self):
        """
        Format nginx conf in a nice way
        """
        self._nginx_formatted_conf = self._formatter.format_string(
            self._inspect_dict(self._nginx_formatted_conf, self._block_dict)
        )
        
    @property
    def built_formatted_config(self):
        """
        Get formatted config
        
        Returns:
        str: formatted nginx config
        """
        return self._nginx_formatted_conf
    
    def _inspect_var(self, conf_str : str, v):
        """
        Process variable
        
        Args:
        conf_str (str): generate config str
        v: value to be processed

        Returns:
        str: Processed value
        """
        return " " + v + ";\n"

    def _inspect_list(self, conf_str : str, l : list):
        """
        Process list
        
        Args:
        conf_str (str): generate config str
        l (list): list to be processed

        Returns:
        str: generated config
        """
        conf_str += " {\n"
        for index, item in enumerate(l):
            if isinstance(item, str) or isinstance(item, int) or isinstance(item, float):
                conf_str += self._inspect_var(conf_str, item)
            elif isinstance(item, list):
                conf_str = self._inspect_list(conf_str, item)
            elif isinstance(item, dict):
                conf_str = self._inspect_dict(conf_str, item)
            else:
                raise Exception(f"{type(item)} is unknown")
        
        return conf_str + "}\n"

    def _inspect_dict(self, conf_str : str, d : dict):
        """
        Process dict
        
        Args:
        conf_str (str): generate config str
        d (dict): value to be processed

        Returns:
        str: generated config
        """
        for key in d.keys():
            v = d.get(key)
            conf_str += str(key) + " "
            if isinstance(v, str) or isinstance(v, int) or isinstance(v, float):
                conf_str += self._inspect_var(conf_str, v)
            elif isinstance(v, list):
                conf_str = self._inspect_list(conf_str, v)
            elif isinstance(v, dict):
                conf_str = self._inspect_dict(conf_str, v)
            else:
                raise Exception(f"{type(v)} is unknown")
        
        return conf_str
