#!/usr/bin/python3

import argparse
import json
import subprocess
from pathlib import Path
import glob
import shutil
import os
import uvicorn
import time

from utils.json_filler import JSONFiller, ProcessedType
from utils.json_builder import JSONBuilder
from utils.callbacks import Callback
from utils.gpg_utils import GPGEncrypt, GPGDecryptAndExtract
from utils.v2ray_config_helper import V2RAYConfigGenerator, ConfigType, EnvInjector
from utils.cast import *

from nginx_conf.nginx_utils import NGINXConfigBlockBuilder, NGINXParser

from constants import *
from monitor import *

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

def nginx_input_conf(input_file_conf, output_file_json):
    nginx_parser = NGINXParser(input_file_conf)
    nginx_parser.extract_config()
    with open(output_file_json, "w+") as f:
        f.write(nginx_parser.as_json)

def nginx_input_json(input_file_json, output_file_conf):
    with open(input_file_json, 'r+') as config_f:
        json_config = json.load(config_f)
        json_filler = JSONFiller(json_config)
        setup_callbacks(json_filler)
        json_filler.fill_json()
        json_config = json_config["conf"]
        
        if isinstance(json_config, dict):
            nginx_builder = NGINXConfigBlockBuilder(json_config)
            nginx_builder.generate_formatted_nginx_config()
            with open(output_file_conf, 'w+') as f:
                f.write(nginx_builder.built_formatted_config)
        elif isinstance(json_config, list):
            with open(output_file_conf, 'w+') as f:
                for item in json_config:
                    nginx_builder = NGINXConfigBlockBuilder(item)
                    nginx_builder.generate_formatted_nginx_config()
                    f.write(nginx_builder.built_formatted_config)
                    f.write("\n")

def nginx(args):
    if (not (args.input_file_conf and args.output_file_json)) and \
            (not (args.input_file_json and args.output_file_conf)):
        raise Exception("Input conf and Output json should pair or Input json and Output conf should pair")
    
    if args.input_file_conf and args.output_file_json:
        nginx_input_conf(args.input_file_conf, args.output_file_json)
        
    elif args.input_file_json and args.output_file_conf:
        nginx_input_json(args.input_file_json, args.output_file_conf)

def copy_root_folder(input_path, output_path):
    if not Path(input_path).exists():
        return
    root_folder = os.path.basename(input_path)
    output_folder = os.path.join(output_path, root_folder)
    shutil.copytree(input_path, output_folder, dirs_exist_ok=True)
    
def backup(args):
    variables = DEVICES[args.device]
    
    Path("./tmp").mkdir(parents=True, exist_ok=True)
    copy_root_folder(variables["V2RAY_ENV_PATH"], "./tmp")
    copy_root_folder(variables["SS_ENV_PATH"], "./tmp")
    copy_root_folder(variables["NGINX_ENV"], "./tmp")
    copy_root_folder(variables["CERT_OUTPUT"], "./tmp")
        
    gp = GPGEncrypt("./tmp", args.output, args.passwd)
    gp.encrypt()
    
    shutil.rmtree("./tmp")
    
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
    
    nginx_env_in = EnvInjector(variables["NGINX_ENV"])
    nginx_env_in.inject_env()
    
    Path(variables["BUILD_CONFIG_OUTPUT"]).mkdir(exist_ok=True, parents=True)
    Path(variables["BUILD_CLIENT_CONFIG_OUTPUT"]).mkdir(exist_ok=True, parents=True)
    Path(variables["NGINX_CONFIG_OUTPUT"]).mkdir(exist_ok=True, parents=True)
    
    # build v2ray configs
    build_config(variables["V2RAY_PATH"], variables["BUILD_CONFIG_OUTPUT"], variables["V2RAY_TYPE"])
    
    # build v2ray client configs
    build_config(variables["V2RAY_CLIENTS_PATH"], variables["BUILD_CLIENT_CONFIG_OUTPUT"], variables["V2RAY_CLIENTS_TYPE"])
    
    # build shadowsocks configs
    build_config(variables["SS_PATH"], variables["BUILD_CONFIG_OUTPUT"], variables["SS_TYPE"])
    
    # build nginx root config
    nginx_input_json(variables["NGINX_ROOT_CONFIG"], variables["NGINX_CONFIG_OUTPUT"] + "nginx_root.conf")
    
    # build nginx server config
    nginx_input_json(variables["NGINX_SERVER_CONFIG"], variables["NGINX_CONFIG_OUTPUT"] + "nginx_server.conf")
    
    # override nginx configs
    if args.nginx:
        root_config = variables["NGINX_CONFIG_OUTPUT"] + "nginx_root.conf"
        server_config = variables["NGINX_CONFIG_OUTPUT"] + "nginx_server.conf"
        os.system(f"cat {root_config} >> /etc/nginx/nginx.conf")
        os.system(f"cat {server_config} > /etc/nginx/sites-available/default")
    
    if args.gen_cert:
        cert_output = variables["CERT_OUTPUT"]
        Path(cert_output).mkdir(exist_ok=True, parents=True)
        for key, value in CERTS.items():
            env = os.environ[key]
            if isinstance(value, list):
                for item in value:
                    cn = env + item[1]
                    print(cn)
                    os.system(f"""openssl req  -nodes -new -x509  -keyout {cert_output}/server{item[0]}.key -out {cert_output}/server{item[0]}.cert \\
                              -subj \"/C=IR/ST=Tehran/L=Tehran/O=Soft98/OU=IT Department/CN={cn}\"""")
  
    v2ray_env_in.remove_env()
    ss_env_in.remove_env()
    nginx_env_in.remove_env()
    
    
def run_monitor_server(args):
    uvicorn.run(app=app, host=args.host, port=int(args.port), log_level="info")
    
    
def monitor(args):
    if (not args.start) and (not args.terminate):
        raise Exception("Eigher start or terminate option should be provided")
    
    if args.terminate:
        path = Path("./monitor.pid")
        if not path.exists():
            raise FileNotFoundError
        
        pid = path.read_text()
        os.kill(int(pid), 9)
    
    elif args.start:
        child_pid = os.fork()
        if child_pid == 0:
            with open("monitor.pid", "w+") as f:
                f.write(str(os.getpid()))
            run_monitor_server(args=args)
            
            
def copy_content(input_path : str, output_path : str):
    if not Path(input_path).exists():
        return
    for item in glob.glob(input_path + "/*"):
        pi = Path(item)
        po = Path(os.path.join(output_path, os.path.basename(item)))
        pop = Path(output_path)
        pop.mkdir(parents=True, exist_ok=True)
        if not pi.exists():
            continue
        env_content = pi.read_text()
        po.write_text(env_content)
            
def setupb(args):
    gpgo = GPGDecryptAndExtract(args.from_input, args.passwd, "./backup")
    gpgo.decrypt_and_extract()
    variables = DEVICES[args.device]
    
    v2ray_env_in = "./backup" + "/" + variables["V2RAY_ENV_PATH"].split("/")[1]
    v2ray_env_out = variables["V2RAY_ENV_PATH"]
    copy_content(v2ray_env_in, v2ray_env_out)

    ss_env_in = "./backup" + "/" + variables["SS_ENV_PATH"].split("/")[1]
    ss_env_out = variables["SS_ENV_PATH"]
    copy_content(ss_env_in, ss_env_out)
    
    nginx_env_in = "./backup" + "/" + variables["NGINX_ENV"].split("/")[1]
    nginx_env_out = variables["NGINX_ENV"]
    copy_content(nginx_env_in, nginx_env_out)
    
    cert_env_in = "./backup" + "/" + variables["CERT_OUTPUT"]
    cert_env_out = variables["CERT_OUTPUT"]
    copy_content(cert_env_in, cert_env_out)

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
    backup_parser.add_argument('--device', choices=['middle', 'end'], required=True)
    backup_parser.add_argument('--output', action='store', type=str, required=False, default="./")
    backup_parser.add_argument('--passwd', action='store', type=str, required=True)
    
    # setup config subparser
    setup_parser = sub_parsers.add_parser("setup")
    setup_parser.set_defaults(func=setup)
    setup_parser.add_argument('--device', choices=['middle', 'end'], required=True)
    setup_parser.add_argument('--gen-cert', action='store_true', required=False)
    setup_parser.add_argument('--nginx', action='store_true', required=False)
    
    # monitor config subparser
    monitor_parser = sub_parsers.add_parser("monitor")
    monitor_parser.set_defaults(func=monitor)
    monitor_parser.add_argument('--start', action='store_true', required=False)
    monitor_parser.add_argument('--terminate', action='store_true', required=False)
    monitor_parser.add_argument('--host', action='store', type=str, required=False, default="127.0.0.1")
    monitor_parser.add_argument('--port', action='store', type=int, required=False, default=8000)
    
    # setupb config subparser
    setupb_parser = sub_parsers.add_parser("setupb")
    setupb_parser.set_defaults(func=setupb)
    setupb_parser.add_argument('--device', choices=['middle', 'end'], required=True)
    setupb_parser.add_argument('--from-input', action='store', required=True)
    setupb_parser.add_argument('--passwd', action='store', type=str, required=True)
    
    args = parser.parse_args()
    args.func(args)
