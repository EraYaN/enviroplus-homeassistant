# enviroplus-homeassistant
Enviro+ MQTT publisher with Home Assistant Discovery written in Python.

## Installign with poetry while using the system python

```
poetry export -f requirements.txt --output requirements.txt
pip3 install -r requirements.txt
```

## Installing with poetry
The `CFLAGS="-fcommon"` is required because of the newer bundled gcc (10).
```
CFLAGS="-fcommon" poetry install
```

## Systemd unit
In for example add a new file at `/etc/systemd/system/enviroplus-homeassistant.service` with the following content:
```
[Unit]
Description=Enviro+ MQTT Home Assistant
After=network.target

[Service]
ExecStart=/home/pi/.cache/pypoetry/virtualenvs/enviroplus-homeassistant-LU5rZJSB-py3.9/bin/python -m enviroplus_homeassistant <arguments>
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