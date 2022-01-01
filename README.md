# enviroplus-homeassistant
Pimoroni Enviro+ MQTT publisher with Home Assistant Discovery written in Python.
Uses [pimoroni/enviroplus-python](https://github.com/pimoroni/enviroplus-python) and the excellent [paho-mqtt](https://www.eclipse.org/paho/index.php?page=clients/python/index.php) client.

Clone this repository to for example your home directory with

```
git clone https://github.com/EraYaN/enviroplus-homeassistant.git
``` 

**Note you might need the package `libatlas3-base` installed with `sudo apt install libatlas3-base` for this to all work at runtime.**
## Installing with pip
```
pip3 install -r requiremnets.txt
```

## Installing with poetry
The `CFLAGS="-fcommon"` is required because of the newer bundled gcc (10) for building `rpi.gpio` which [piwheels](https://piwheels.org) does not build for python 3.9 that ships with bullseye.
```
CFLAGS="-fcommon" poetry install
```

## SystemD unit
Run `poetry run bash -c 'which python3'` to get the python path in the virtual env. If you are using the system python it is most likely `/usr/bin/python3`
Add a new file `/etc/systemd/system/enviroplus-homeassistant.service` with the following content and replace the `<`*tags*`>`.
```
[Unit]
Description=Enviro+ MQTT Home Assistant
After=network.target

[Service]
ExecStart=<python_path> -m enviroplus_homeassistant <arguments>
WorkingDirectory=/home/pi/enviroplus-homeassistant
StandardOutput=inherit
StandardError=inherit
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
```
and then 
```
sudo systemctl enable enviroplus-homeassistant.service
sudo systemctl start enviroplus-homeassistant.service
```