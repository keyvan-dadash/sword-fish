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
    ("-web", 0),
    ("-trojan", 1),
    ("-grpc", 2),
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

def handle_json_dir(output_file_path : Path, config_folder_path_str : str):
    jsb = JSONBuilder(config_folder_path_str, structure)
    jsb.gather_all_files()
    jsb.build_json()
    output_file_path.parent.mkdir(parents=True, exist_ok=True)
    output_file_path.write_text(jsb.built_json)
    
    print(jsb.built_json)

def handle_json_file(output_file_path : Path, config_file_path_str : str):
    with open(config_file_path_str, "r+") as f:
        jsf = JSONFiller(json.load(f))
        setup_callbacks(jsf)
        jsf.fill_json()
        output_file_path.parent.mkdir(parents=True, exist_ok=True)
        json_out = json.dumps(jsf.filled_json, indent=2)
        output_file_path.write_text(json_out)
    
        print(json_out)

def main(args):
    
    if args.json_dir is None and args.json_file is None:
        raise Exception("Eigher json-dir or json-file should present")
    
    if args.json_dir:
        config_path = Path(args.json_dir)
        config_folder_path_str = args.json_dir
        output_file_path = Path(args.output_dir + "/" + config_path.name + ".json")
        if not config_path.exists():
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), args.json_dir)
        if config_path.is_file():
            raise Exception("Specified json dir is not a folder")
        handle_json_dir(output_file_path, config_folder_path_str)
        
    elif args.json_file:
        config_file = Path(args.json_file)
        config_file_path_str = args.json_file
        output_file_path = Path(args.output_dir + "/" + config_file.name)
        if not config_file .exists():
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), args.json_dir)
        if not config_file.is_file():
            raise Exception("Specified json dir is not a file")
        handle_json_file(output_file_path, config_file_path_str)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Replace all variables inside json with with env variable')

    parser.add_argument('--json-dir', action='store', type=str, required=False)
    parser.add_argument('--json-file', action='store', type=str, required=False)
    
    parser.add_argument('--output-dir', action='store', type=str, required = True)

    args = parser.parse_args()
    main(args)
