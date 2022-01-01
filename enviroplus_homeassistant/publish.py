# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from ctypes import ArgumentError
import logging
import paho.mqtt.client as mqtt
import json, dataclasses
from .helpers import del_none

logging.basicConfig(level=logging.DEBUG)

class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return del_none(dataclasses.asdict(o).copy())
        return super().default(o)

class MqttPublisher:
    def __init__(self, client_id, host, port, username, password, use_tls, on_connect = None):
        if not callable(on_connect):
            raise ArgumentError("on_connect callback should be a function.")
        self.on_connect = on_connect

        self.connection_error = None
        self.client = mqtt.Client(client_id=client_id)
        self.client.on_connect = self.__on_connect
        self.client.username_pw_set(username, password)
        logger = logging.getLogger(__name__)
        self.client.enable_logger(logger)
        if use_tls:
            self.client.tls_set()
        self.client.connect(host, port)
        self.client.loop_start()

    def __on_connect(self, client, userdata, flags, rc):
        errors = {
            1: "incorrect MQTT protocol version",
            2: "invalid MQTT client identifier",
            3: "server unavailable",
            4: "bad username or password",
            5: "connection refused"
        }

        if rc > 0:
            self.connection_error = errors.get(rc, "unknown error")
        else:
            if self.on_connect:
                self.on_connect(self, userdata, flags)

    def publish(self, topic, value, retain=False):
        self.client.publish(topic, str(value),retain=retain)

    def publish_json(self, topic, obj, retain=False):
        self.publish(topic, json.dumps(obj,cls=EnhancedJSONEncoder),retain=retain)

    def destroy(self):
        self.client.disconnect()
        self.client.loop_stop()
