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
from utils.gpg_utils import GPGEncrypt
from utils.v2ray_config_helper import V2RAYConfigGenerator, ConfigType, EnvInjector
from utils.cast import *

from nginx_conf.nginx_utils import NGINXConfigBlockBuilder, NGINXParser

from constants import *

def setup_callbacks(json_f : JSONFiller):
        c = Callback(GLOBAL_VARS, SPECILIZED_VARS)
        c.setup_callback(json_f)
        
structure = [
    ("log", setup_callbacks),
    ("inbounds", setup_callbacks),
    ("outbounds", setup_callbacks),
    ("routing", setup_callbacks)
]

def v2ray(args):
    if args.json_dir is None and args.json_file is None:
        raise Exception("Eigher json-dir or json-file should present")
    
    config_gen = None
    if args.json_dir:
        config_gen = V2RAYConfigGenerator(args.json_dir, args.output_dir, ConfigType.DIR, structure, setup_callbacks)
    elif args.json_file:
        config_gen = V2RAYConfigGenerator(args.json_file, args.output_dir, ConfigType.FILE, structure, setup_callbacks)
        
    config_gen.build_configs()

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

def backup(args):
    if (not args.middle_path) and (not args.end_path):
        raise Exception("Either middle or end path should specified")
    
    if args.middle_path:
        input_path = args.middle_path
    elif args.end_path:
        input_path = args.end_path
        
    gp = GPGEncrypt(input_path, args.output, args.passwd)
    gp.encrypt()
    
def is_file(type : str):
    if "File" not in type:
        return True
    return False

def build_config(path_to_config : str, output_config : str, config_type : str):
    file_type = ConfigType.FILE
    if not is_file(config_type):
        file_type = ConfigType.DIR
    for item in glob.glob(path_to_config + "/*"):
        config_gen = V2RAYConfigGenerator(
            item,
            output_config,
            file_type,
            structure,
            setup_callbacks)
        config_gen.build_configs()

def setup(args):
    variables = DEVICES[args.device]
    v2ray_env_in = EnvInjector(variables["V2RAY_ENV_PATH"])
    v2ray_env_in.inject_env()

    ss_env_in = EnvInjector(variables["SS_ENV_PATH"])
    ss_env_in.inject_env()
    
    Path(variables["BUILD_CONFIG_OUTPUT"]).mkdir(exist_ok=True, parents=True)
    Path(variables["BUILD_CLIENT_CONFIG_OUTPUT"]).mkdir(exist_ok=True, parents=True)
    
    # build v2ray configs
    build_config(variables["V2RAY_PATH"], variables["BUILD_CONFIG_OUTPUT"], variables["V2RAY_TYPE"])
    
    # build v2ray client configs
    build_config(variables["V2RAY_CLIENTS_PATH"], variables["BUILD_CLIENT_CONFIG_OUTPUT"], variables["V2RAY_CLIENTS_TYPE"])
    
    # build shadowsocks configs
    build_config(variables["SS_PATH"], variables["BUILD_CONFIG_OUTPUT"], variables["SS_TYPE"])
  
    v2ray_env_in.remove_env()
    ss_env_in.remove_env()

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
    
    # backup config subparser
    backup_parser = sub_parsers.add_parser("backup")
    backup_parser.set_defaults(func=backup)
    backup_parser.add_argument('--middle-path', action='store', type=str, required=False)
    backup_parser.add_argument('--end-path', action='store', type=str, required=False)
    backup_parser.add_argument('--output', action='store', type=str, required=True)
    backup_parser.add_argument('--passwd', action='store', type=str, required=True)
    
    setup_parser = sub_parsers.add_parser("setup")
    setup_parser.set_defaults(func=setup)
    setup_parser.add_argument('--device', choices=['middle', 'end'], required=True)
    
    args = parser.parse_args()
    args.func(args)
