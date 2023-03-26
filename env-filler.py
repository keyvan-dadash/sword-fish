#!/usr/bin/python3

import os
import re
import argparse
import copy
import json
from pathlib import Path
import errno
import glob
from utils.json_filler import JSONFiller, ProcessedType
from utils.json_builder import JSONBuilder
from utils.callbacks import Callback
from utils.cast import *

vars = [
    ("", 0),
    ("-web", 1),
    ("-trojan", 2),
    ("-grpc", 3),
]

def setup_callbacks(json_f : JSONFiller):
        c = Callback(vars)
        c.setup_callback(json_f)
        
structure = [
    ("log", setup_callbacks),
    ("inbounds", setup_callbacks),
    ("outbounds", setup_callbacks),
    ("routing", setup_callbacks)
]

def main(args):
    
    config_path = Path(args.json_dir)
    config_folder_path_str = args.json_dir
    output_file_path = Path(args.output_dir + "/" + config_path.name + ".json")
    
    if not config_path.exists():
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), args.json_dir)
    if config_path.is_file():
        raise Exception("Specified json dir is not a folder")

    jsb = JSONBuilder(config_folder_path_str, structure)

    jsb.gather_all_files()
    jsb.build_json()
    
    output_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    output_file_path.write_text(jsb.built_json)

    print(jsb.built_json)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Replace all variables inside json with with env variable')

    parser.add_argument('--json-dir', action='store', type=str, required=True)
    parser.add_argument('--output-dir', action='store', type=str, required = True)

    args = parser.parse_args()
    main(args)
