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
