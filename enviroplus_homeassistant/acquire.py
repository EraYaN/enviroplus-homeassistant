# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import collections, threading, traceback

try:
    # Transitional fix for breaking change in LTR559
    from ltr559 import LTR559
    ltr559 = LTR559()
except ImportError:
    import ltr559

from bme280 import BME280
from pms5003 import PMS5003
from enviroplus import gas
from atmos import calculate

class EnviroPlus:
    def __init__(self, use_pms5003, num_samples, use_cpu_comp:bool=True, cpu_num_samples:int=5, cpu_comp_factor:float=2.25):
        self.bme280 = BME280()

        self.samples = collections.deque(maxlen=num_samples)
        self.use_cpu_comp=use_cpu_comp
        if self.use_cpu_comp>0:
            self.cpu_comp_factor=cpu_comp_factor
            self.cpu_samples = collections.deque(maxlen=cpu_num_samples)
        else:
            self.cpu_comp_factor = None
            self.cpu_samples = None

        self.latest_pms_readings = {}

        if use_pms5003:
            self.pm_thread = threading.Thread(target=self.__read_pms_continuously)
            self.pm_thread.daemon = True
            self.pm_thread.start()

    def __read_pms_continuously(self):
        """Continuously reads from the PMS5003 sensor and stores the most recent values
        in `self.latest_pms_readings` as they become available.

        If the sensor is not polled continously then readings are buffered on the PMS5003,
        and over time a significant delay is introduced between changes in PM levels and 
        the corresponding change in reported levels."""

        pms = PMS5003()
        while True:
            try:
                pm_data = pms.read()
                self.latest_pms_readings = {
                    "pm1": pm_data.pm_ug_per_m3(1.0, atmospheric_environment=True),
                    "pm25": pm_data.pm_ug_per_m3(2.5, atmospheric_environment=True),
                    "pm10": pm_data.pm_ug_per_m3(None, atmospheric_environment=True),
                }
            except:
                print("Failed to read from PMS5003. Resetting sensor.")
                traceback.print_exc()
                pms.reset()


    def take_readings(self):
        gas_data = gas.read_all()
        readings = {
            #"proximity": ltr559.get_proximity(),
            "illuminance": ltr559.get_lux(),
            "temperature": self.bme280.get_temperature(),
            "pressure": self.bme280.get_pressure(),
            "humidity": self.bme280.get_humidity(),
            "gas_oxidising": gas_data.oxidising / 1e3, #kOhm
            "gas_reducing": gas_data.reducing / 1e3, #kOhm
            "gas_nh3": gas_data.nh3 / 1e3, #kOhm
        }

        if self.use_cpu_comp:
            readings = self.compensate_readings(readings)

        readings.update(self.latest_pms_readings)
        
        return readings

    def compensate_readings(self, readings):
        self.cpu_samples.append(self.get_cpu_temperature())
        
        avg_cpu_temp = sum(self.cpu_samples) / float(len(self.cpu_samples))

        t_precomp = readings["temperature"] # RH source temp

        readings["temperature"] = readings["temperature"] - ((avg_cpu_temp - readings["temperature"]) / self.cpu_comp_factor)

        ah = calculate('AH', RH=readings["humidity"], p=readings['pressure'], p_unit="hPa", T=t_precomp, T_unit="degC")
        rh_comp = calculate('RH', AH=ah, p=readings['pressure'], p_unit="hPa", Tv=readings["temperature"], Tv_unit="degC") # Using the virtual temperature is close enough
        readings["humidity"] = rh_comp

        return readings

    def update(self):
        self.samples.append(self.take_readings())

    def get_cpu_temperature(self):
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp = f.read()
            temp = int(temp) / 1000.0
        return temp

