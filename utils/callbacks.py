import copy

from .cast import *
from .json_filler import JSONFiller, ProcessedType

class Callback():
    def __init__(self, general_new_vars : list, specialized_vars : dict = None) -> None:
        """
        Initialize Callback object.

        Args:
        general_new_vars (list): a list which guid callback how to replicate the configs
        specialized_vars (dict): a dict of specialized variables which do not follow the pattern of general_new_vars
        """
        self._vars = {}
        self._new_vars = general_new_vars
        self._spec_vars = specialized_vars
        self._depth = []
        self._current_depth = 0
        self._index = 0
        self._last_list : list = []
        
    def _dict_callback(self, val : dict):
        """
        Callback to be called when encounter a dict
        
        Args:
        val: value to be processed

        Returns:
        dict: Processed dict
        """
        self._current_depth += 1
        comment = val.get("_comment", None) # when encounter _comment key inside dict, it is mean that we should replicate this dict
        if comment != None and "HERE" in comment: # only when HERE is inside the _commnet key we should process and replicate.
            val["_comment"] = "FINISH" # it is like a signal for later use
            if len(self._last_list) == 0: # if the dict was not in a list
                js = JSONFiller(val)
                jsb = type(self)(self._new_vars, self._spec_vars)
                jsb.setup_callback(js)
                js.fill_json()
                val = js.filled_json
            else: # if we encounter a list before
                index_of_elem = self._last_list[-1].index(val)
                for i in range(len(self._new_vars) - 1):
                    self._last_list[-1].insert(index_of_elem, copy.deepcopy(val)) # replicate dict inside the list
                js = JSONFiller(self._last_list[-1])
                jsb = type(self)(self._new_vars, self._spec_vars)
                jsb.setup_callback(js)
                js.fill_json()
                self._last_list[-1] = js.filled_json
        return val
    
    def _list_callback(self, val):
        """
        Callback to be called when encounter a list
        
        Args:
        val: value to be processed

        Returns:
        list: Processed list
        """
        self._last_list.append(val)
        return val
    
    def _str_callback(self, val):
        """
        Callback to be called when encounter a string
        
        Args:
        val: value to be processed

        Returns:
        str: Processed string
        """
        return val
    
    def _val_callback(self, val_name, val):
        """
        Callback to be called when encounter a env variable
        
        Args:
        val: value to be processed

        Returns:
        val: Processed value
        """
        specilized_var_name = val_name.split("_VAR_") # we detect special variable when they have this pattern: {something}_VAR_{variable_name}
        if len(specilized_var_name) > 1:
            var_list = self._spec_vars[specilized_var_name[1]]
            var = var_list[self._index % len(var_list)]
        else:
            var = self._new_vars[self._index % len(self._new_vars)]
        if can_be_int(val):
            val = str(int(val) + var[1])
        else:
            val = str(val) + str(var[0])
        return val
    
    def _end_process(self, val, type):
        """
        Callback to be called process of a obj finished
        
        Args:
        val: value to be processed
        type: type of processed value

        Returns:
        val: Processed value
        """
        if type == ProcessedType.DICT:
            self._current_depth -= 1
            comment = val.get("_comment", None)
            if self._current_depth <= 0 and comment != None and "FINISH" in comment: # if _comment present and processed
                val.pop("_comment") # we pop the comment
                self._index += 1 # we advance to the next general variable
        elif type == ProcessedType.LIST:
            self._last_list.pop()
        return val
    
    def _eligible_val(self, val_name):
        """
        Callback to check whether the given variable name is eligiable for being process or not
        
        Args:
        val_name: variable name to be process

        Returns:
        boolean: eligibility of variable
        """
        if "VAR" in val_name: # variable is eligible if it have VAR inside it
            return True
        return False
        
    def setup_callback(self, json_f : JSONFiller):
        """
        Setup all callback function in json_f
        
        Args:
        json_f: a JSONFiller objet
        """
        self._json_f = json_f
        self._json_f.set_callback_on_dict(self._dict_callback)
        self._json_f.set_callback_on_list(self._list_callback)
        self._json_f.set_callback_on_str(self._str_callback)
        self._json_f.set_callback_on_val(self._val_callback)
        self._json_f.set_callback_end_of_process(self._end_process)
        self._json_f.set_callback_eligible(self._eligible_val)