#!/usr/bin/python3

import os
import re
import argparse
import copy
import json
from pathlib import Path
from functools import wraps
import errno
import glob

from utils.json_filler import JSONFiller, ProcessedType
from utils.json_builder import JSONBuilder
from utils.callbacks import Callback
from utils.cast import *

from nginx_conf.nginx_utils import NGINXConfigBlockBuilder, NGINXParser

vars = [
    ("-web", 0),
    ("-trojan", 1),
    ("-grpc", 2),
]

spec_var = {
    "SNI": [
        (".soft98.ir", 0),
        (".mci.ir", 1),
        (".downloadha.ir", 2),
    ]
}

def setup_callbacks(json_f : JSONFiller):
        c = Callback(vars, spec_var)
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


def v2ray(args):
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

def nginx(args):
    if (not (args.input_file_conf and args.output_file_json)) and \
            (not (args.input_file_json and args.output_file_conf)):
        raise Exception("Input conf and Output json should pair or Input json and Output conf should pair")
    
    if args.input_file_conf and args.output_file_json:
        nginx_parser = NGINXParser(args.input_file_conf)
        nginx_parser.extract_config()
        with open(args.output_file_json, "w+") as f:
            f.write(nginx_parser.as_json)
        
    elif args.input_file_json and args.output_file_conf:
        with open(args.input_file_json, 'r+') as config_f:
                json_config = json.load(config_f)
                json_filler = JSONFiller(json_config)
                setup_callbacks(json_filler)
                json_filler.fill_json()
                json_config = json_config["conf"]
                
                if isinstance(json_config, dict):
                    nginx_builder = NGINXConfigBlockBuilder(json_config)
                    nginx_builder.generate_formatted_nginx_config()
                    with open(args.output_file_conf, 'w+') as f:
                        f.write(nginx_builder.built_formatted_config)
                elif isinstance(json_config, list):
                    with open(args.output_file_conf, 'w+') as f:
                        for item in json_config:
                            nginx_builder = NGINXConfigBlockBuilder(item)
                            nginx_builder.generate_formatted_nginx_config()
                            f.write(nginx_builder.built_formatted_config)
                            f.write("\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Sword fish cli')
    sub_parsers = parser.add_subparsers(help='sub-command help')
    
    # v2ray config subparser
    v2ray_parser = sub_parsers.add_parser("v2ray")
    v2ray_parser.set_defaults(func=v2ray)
    v2ray_parser.add_argument('--json-dir', action='store', type=str, required=False)
    v2ray_parser.add_argument('--json-file', action='store', type=str, required=False)
    v2ray_parser.add_argument('--output-dir', action='store', type=str, required = True)
    
    # nginx config subparser
    nginx_parser = sub_parsers.add_parser("nginx")
    nginx_parser.set_defaults(func=nginx)
    nginx_parser.add_argument('--input-file-conf', action='store', type=str, required=False)
    nginx_parser.add_argument('--output-file-conf', action='store', type=str, required=False)
    nginx_parser.add_argument('--input-file-json', action='store', type=str, required=False)
    nginx_parser.add_argument('--output-file-json', action='store', type=str, required=False)
    
    args = parser.parse_args()
    args.func(args)
