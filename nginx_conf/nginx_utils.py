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
        self._config_path = nginx_config_path
        self._extracted_config : nginx.Conf = None
    
    def extract_config(self):
        self._extracted_config = nginx.loadf(self._config_path)
        
    @property
    def as_json(self):
        return json.dumps(self._extracted_config.as_dict, indent=2)
        
    @property
    def as_dict(self):
        return self._extracted_config.as_dict

class NGINXConfigBlockBuilder():
    
    def __init__(self, block_dict : dict):
        self._nginx_formatted_conf = ""
        self._block_dict = block_dict
        self._formatter = Formatter()
    
    def generate_formatted_nginx_config(self):
        self._nginx_formatted_conf = self._formatter.format_string(
            self._inspect_dict(self._nginx_formatted_conf, self._block_dict)
        )
        
    @property
    def built_formatted_config(self):
        return self._nginx_formatted_conf
    
    def _inspect_var(self, conf_str : str, v):
        return " " + v + ";\n"

    def _inspect_list(self, conf_str : str, l : list):
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


# json_str = json.dumps(c.as_dict, indent=2)

# print(json_str)

# dd = json.loads(json_str)["conf"]
# print(dd[0])

# nginx_conf = generate_nginx_config_from_dict(dd[0])

# f = Formatter()

# print(f.format_string(nginx_conf))

# print(json.dumps(c.as_dict))
# print(c.as_strings)

# s = nginx.loads(json.dumps(c.as_dict))

# print(nginx.dumps(c))
# print(''.join(json.dumps(c.as_dict)))