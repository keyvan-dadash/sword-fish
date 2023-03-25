#!/usr/bin/bash

mkdir -p /etc/systemd/system/docker.service.d

sed 's/-proxy-/'"$1"'/g' http-proxy-temp.conf > http-proxy.conf

cp http-proxy.conf /etc/systemd/system/docker.service.d/

systemctl daemon-reload
