# Sword Fish

Sword Fish is a project in order to facilitate setting up a proxy platfrom, with the help of v2fly, in order to bring multiple way to bypass government's censhorship.

## Setup
For setting up Sword Fish you have do the following steps:

```bash
apt install git nginx python3 python3-pip python3-gnupg
```

Install docker from home page.

Before starting up Sword Fish you must choose your device. There are two type of devices:

#### Middle:

This is for the case when you have middle point which have fewer restriction due to cenchosrship, and it is capable of tranfering your traffic with greater speed and less latency,
but this device do not have access to the free internet. Therefore, it is usefull for the case when you can connect to this device more easier than the end device.

#### End:

This is the device which have access to the free internet without any restriciton.

After choosing your device you have to fillout the related env files inside the choosed device.

Then use the Sword Fish cli to settup the project:

```bash
./sword-fish.py setup --help             
usage: sword-fish.py setup [-h] --device {middle,end} [--gen-cert] [--nginx]

options:
  -h, --help            show this help message and exit
  --device {middle,end}
                        type of device to use
  --gen-cert            genrate the necessary certificates for the sword fish
  --nginx               change host nginx configs

```


