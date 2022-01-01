# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from dataclasses import dataclass, field, InitVar
from typing import List, Union, Tuple
from .helpers import slugify

@dataclass
class DiscoveryDeviceConfig:
    """Class for the discovery config of a device."""

    name:str = None
    model:str = None
    manufacturer:str = None
    sw_version:str = None
    identifiers:Union[str,List[str]] = None
    connections:List[Tuple[str,str]] = field(default_factory=list)
    configuration_url:str = None
    suggested_area:str= None
    via_device:str=None

@dataclass
class DiscoverySensorConfig:
    """Class for the discovery config of a sensor."""

    client_id:InitVar[str]
    prefix:InitVar[str]

    name:str
    device:DiscoveryDeviceConfig
    device_class:str = None
    unit_of_measurement:str = None
    value_template:str="{{ value_json.value | round(1) }}"
    expire_after: int = 15*60
    force_update: bool = True
    state_class: str = "measurement"

    object_id: str = field(init=False)
    unique_id:str = field(init=False)
    state_topic: str = field(init=False)
    
    def __post_init__(self, client_id:str,prefix:str=None):
        if self.device:
            self.object_id = f"{slugify(self.device.name)}_{slugify(self.name)}"
        else:
            self.object_id = slugify(self.name)
        self.state_topic = self.get_base_topic(client_id,prefix) + "/state"
        
         
        self.unique_id = f"{client_id}_{slugify(self.name)}"

    def get_base_topic(self,client_id:str=None,prefix:str=None):
        if prefix:
            if not prefix.endswith("/"):
                prefix += "/"
        if client_id:
            if not client_id.endswith("/"):
                client_id += "/"
        return f"{prefix or ''}sensor/{client_id or ''}{slugify(self.name)}"

    def get_config_topic(self,client_id:str=None,prefix:str=None):
        return self.get_base_topic(client_id,prefix) + "/config"
    

@dataclass
class SensorPayload:
    """Class for the payload of a sensor."""
    value: Union[str,int,float]
