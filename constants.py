GLOBAL_VARS = [
    ("-web", 0),
    ("-trojan", 1),
    ("-grpc", 2),
]

SPECILIZED_VARS = {
    "SNI" : [
        (".soft98.ir", 0),
        (".mci.ir", 1),
        (".downloadha.ir", 2),
    ]
}

DEVICES = {
    "middle" : {
        "V2RAY_ENV_PATH": "middle-point/v2ray-configs-env",
        "V2RAY_ENV_TYPE": "File",
        
        "V2RAY_PATH": "middle-point/v2ray-configs",
        "V2RAY_TYPE": "Dir",
        
        "V2RAY_CLIENTS_PATH": "middle-point/v2ray-configs-client",
        "V2RAY_CLIENTS_TYPE": "File",
        
        "SS_ENV_PATH": "middle-point/shadowsocks-configs-env",
        "SS_ENV_TYPE": "File",
        
        "SS_PATH": "middle-point/shadowsocks-configs",
        "SS_TYPE": "File",
        
        "BUILD_CONFIG_OUTPUT": "build-configs/",
        "BUILD_CLIENT_CONFIG_OUTPUT": "client-configs/",
        
        "NGINX_SERVER_CONFIG": "nginx_conf/sword-fish-nginx-middle.json",
        "NGINX_ROOT_CONFIG": "nginx_conf/sword-fish-nginx-root-middle.json",
        "NGINX_CONFIG_OUTPUT": "build-nginx-configs/",
        "NGINX_ENV": "nginx_conf/",
    },
    "end" : {
        "V2RAY_ENV_PATH": "end-point/v2ray-configs-env",
        "V2RAY_ENV_TYPE": "File",
        
        "V2RAY_PATH": "end-point/v2ray-configs",
        "V2RAY_TYPE": "File",
        
        "V2RAY_CLIENTS_PATH": "middle-point/v2ray-configs-client",
        "V2RAY_CLIENTS_TYPE": "File",
        
        "SS_ENV_PATH": "end-point/shadowsocks-configs-env",
        "SS_ENV_TYPE": "File",
        
        "SS_PATH": "end-point/shadowsocks-configs",
        "SS_TYPE": "File",
        
        "BUILD_CONFIG_OUTPUT": "build-configs/",
        "BUILD_CLIENT_CONFIG_OUTPUT": "client-configs/",
        
        "NGINX_SERVER_CONFIG": "nginx_conf/sword-fish-nginx-end.json",
        "NGINX_ROOT_CONFIG": "nginx_conf/sword-fish-nginx-root-end.json",
        "NGINX_CONFIG_OUTPUT": "build-nginx-configs/",
        "NGINX_ENV": "nginx_conf/",
    },
}