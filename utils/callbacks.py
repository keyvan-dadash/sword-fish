import copy

from .cast import *
from .json_filler import JSONFiller, ProcessedType

class Callback():
    def __init__(self, new_vars : list) -> None:
        self._vars = {}
        self._new_vars = new_vars
        self._depth = []
        self._current_depth = 0
        self._index = 0
        self._last_list : list = []
        
    def _dict_callback(self, val : dict):
        self._current_depth += 1
        comment = val.get("_comment", None)
        if comment != None and "HERE" in comment:
            val["_comment"] = "FINISH"
            if len(self._last_list) == 0:
                js = JSONFiller(val)
                jsb = type(self)(self._new_vars)
                jsb.setup_callback(js)
                js.fill_json()
                val = js.filled_json
            else:
                for i in range(len(self._new_vars) - 1):
                    self._last_list[-1].append(copy.deepcopy(val))
                js = JSONFiller(self._last_list[-1])
                jsb = type(self)(self._new_vars)
                jsb.setup_callback(js)
                js.fill_json()
                self._last_list[-1] = js.filled_json
        return val
    
    def _list_callback(self, val):
        self._last_list.append(val)
        return val
    
    def _str_callback(self, val):
        return val
    
    def _val_callback(self, val):
        var = self._new_vars[self._index % len(self._new_vars)]
        if can_be_int(val):
            val = str(int(val) + var[1])
        else:
            val = str(val) + str(var[0])
        return val
    
    def _end_process(self, val, type):
        if type == ProcessedType.DICT:
            self._current_depth -= 1
            comment = val.get("_comment", None)
            if self._current_depth <= 0 and comment != None and "FINISH" in comment:
                val.pop("_comment")
                self._index += 1
        elif type == ProcessedType.LIST:
            self._last_list.pop()
        return val
    
    def _eligible_val(self, val_name):
        if "VAR" in val_name:
            return True
        return False
        
    def setup_callback(self, json_f : JSONFiller):
        self._json_f = json_f
        self._json_f.set_callback_on_dict(self._dict_callback)
        self._json_f.set_callback_on_list(self._list_callback)
        self._json_f.set_callback_on_str(self._str_callback)
        self._json_f.set_callback_on_val(self._val_callback)
        self._json_f.set_callback_end_of_process(self._end_process)
        self._json_f.set_callback_eligible(self._eligible_val)