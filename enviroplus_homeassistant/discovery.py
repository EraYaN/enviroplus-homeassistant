# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import re, uuid,platform

from .publish import MqttPublisher
from .models import DiscoveryDeviceConfig, DiscoverySensorConfig
from .helpers import slugify

class HassDiscovery:
    def __init__(self, client_id:str = None, prefix:str="homeassistant", use_pms5003:bool = True, retain: bool=True):
        self.mac = ':'.join(re.findall('..', '%012x' % uuid.getnode()))
        self.serialnum = self.getserial()
        self.use_pms5003 = use_pms5003
        self.prefix=prefix
        self.retain = retain
        
        self.device = DiscoveryDeviceConfig(
            name="AirQuality",
            model="Enviro+ on Raspbery Pi Zero W 2",
            manufacturer="Pimoroni & Raspberry Pi Foundation",
            sw_version=platform.platform(),
            connections=[['mac',self.mac]],
            identifiers=[self.serialnum]
        )

        if client_id:
            self.client_id = client_id
        else:
            self.client_id = slugify(self.device.name)+"_"+self.serialnum.strip('0')

        self.sensors = {
            "humidity": DiscoverySensorConfig(
                client_id=self.client_id,
                prefix=self.prefix,
                name="Humidity",
                unit_of_measurement="%",
                device=self.device,
                device_class="humidity"
            ),
            "temperature": DiscoverySensorConfig(
                client_id=self.client_id,
                prefix=self.prefix,
                name="Temperature",
                unit_of_measurement="°C",
                device=self.device,
                device_class="temperature"
            ),
            "pressure":  DiscoverySensorConfig(
                client_id=self.client_id,
                prefix=self.prefix,
                name="Pressure",
                unit_of_measurement="hPa",
                device=self.device,
                device_class="pressure"
            ),
            "illuminance":  DiscoverySensorConfig(
                client_id=self.client_id,
                prefix=self.prefix,
                name="Illuminance",
                unit_of_measurement="lx",
                device=self.device,
                device_class="illuminance"
            ),
            "gas_oxidising":  DiscoverySensorConfig(
                client_id=self.client_id,
                prefix=self.prefix,
                name="Gas Oxidising",
                unit_of_measurement="kOhm",
                device=self.device
            ),
            "gas_reducing":  DiscoverySensorConfig(
                client_id=self.client_id,
                prefix=self.prefix,
                name="Gas Reducing",
                unit_of_measurement="kOhm",
                device=self.device
            ),
            "gas_nh3":  DiscoverySensorConfig(
                client_id=self.client_id,
                prefix=self.prefix,
                name="Gas NH3",
                unit_of_measurement="kOhm",
                device=self.device
            ),
            "pm1":  DiscoverySensorConfig(
                client_id=self.client_id,
                prefix=self.prefix,
                name="Particulate PM1",
                unit_of_measurement="µg/m³",
                device=self.device,
                device_class="pm1"
            ),
            "pm25":  DiscoverySensorConfig(
                client_id=self.client_id,
                prefix=self.prefix,
                name="Particulate PM2.5",
                unit_of_measurement="µg/m³",
                device=self.device,
                device_class="pm25"
            ),
            "pm10":  DiscoverySensorConfig(
                client_id=self.client_id,
                prefix=self.prefix,
                name="Particulate PM10",
                unit_of_measurement="µg/m³",
                device=self.device,
                device_class="pm10"
            )
        }

    def publish(self, publisher, userdata, flags):
        for sensor_name, sensor in self.sensors.items():
            self.publish_config(publisher,sensor)
        
    def publish_config(self, publisher, sensor:DiscoverySensorConfig):
        publisher.publish_json(sensor.get_config_topic(self.client_id,self.prefix), sensor, retain=self.retain)

    def publish_delete(self, publisher, userdata, flags):
        for sensor_name, sensor in self.sensors.items():
            publisher.publish(sensor.get_config_topic(self.client_id,self.prefix),'', retain=self.retain)

    def getserial(self):
        # Extract serial from cpuinfo file
        cpuserial = "0000000000000000"
        try:
            f = open('/proc/cpuinfo','r')
            for line in f:
                if line[0:6]=='Serial':
                    cpuserial = line[10:26]
            f.close()
        except:
            cpuserial = "000000000ERROR"

        return cpuserial

