# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import argparse, time, sys, logging

from enviroplus_homeassistant.models import SensorPayload

logging.basicConfig(level=logging.INFO)

from .publish import MqttPublisher
from .discovery import HassDiscovery
from .acquire import EnviroPlus

def parse_args():
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("-h", "--host", required=True, help="the MQTT host to connect to")
    ap.add_argument("-p", "--port", type=int, default=1883, help="the port on the MQTT host to connect to")
    ap.add_argument("-U", "--username", default=None, help="the MQTT username to connect with")
    ap.add_argument("-P", "--password", default=None, help="the password to connect with")
    ap.add_argument("--delete-sensors", action="store_true", help="Delete sensors in home assistant")
    ap.add_argument("--print-sensors", action="store_true", help="Print sensors and do nothing else")
    ap.add_argument("--prefix", default="homeassistant", help="the topic prefix to use when publishing readings, i.e. 'homeassistant'")
    ap.add_argument("--client-id", default="", help="the MQTT client identifier to use when connecting")
    ap.add_argument("--interval", type=int, default=5, help="the duration in seconds between updates")
    ap.add_argument("--delay", type=int, default=15, help="the duration in seconds to allow the sensors to stabilise before starting to publish readings")
    ap.add_argument("--use-pms5003", action="store_true", help="if set, PM readings will be taken from the PMS5003 sensor")
    ap.add_argument("--use-cpu-comp", action="store_true", help="Use the CPU temp compensation.")
    ap.add_argument("--no-retain-config", dest='retain_config', action="store_false", help="Do not set RETAIN flag on config messages.")
    ap.add_argument("--retain-state", action="store_true", help="Set RETAIN flag on state messages.")
    ap.add_argument("--cpu-comp-factor", type=float, default=2.25, help="The factor to use for the CPU temp compensation. Decrease this number to adjust the temperature down, and increase to adjust up.")
    ap.add_argument("--help", action="help", help="print this help message and exit")
    return vars(ap.parse_args())


def main():
    args = parse_args()

    logging.info("Starting with arguments: %s", args)

    discovery = HassDiscovery(
        use_pms5003=args["use_pms5003"],
        prefix=args["prefix"],
        retain=args["retain_config"]
    )

    if args['print_sensors']:
        for sensor in discovery.sensors:
            print("Key: ",sensor)
            print("Payload: ",discovery.sensors[sensor])
            print("Config Topic:",discovery.sensors[sensor].get_config_topic(discovery.client_id,discovery.prefix))
        exit()

    # Initialise the publisher
    publisher = MqttPublisher(
        client_id=args["client_id"],
        host=args["host"],
        port=args["port"],
        username=args["username"],
        password=args["password"],
        use_tls=True,
        on_connect=discovery.publish if not args['delete_sensors'] else discovery.publish_delete
    )

    if args['delete_sensors']:
        time.sleep(args["delay"])
        exit()

    acquire = EnviroPlus(
        use_pms5003=args["use_pms5003"],
        num_samples=args["interval"],
        use_cpu_comp=args["use_cpu_comp"],
        cpu_comp_factor=args["cpu_comp_factor"]
    )

    # Take readings without publishing them for the specified delay period,
    # to allow the sensors time to warm up and stabilise
    publish_start_time = time.time() + args["delay"]
    while time.time() < publish_start_time:
        acquire.update()
        time.sleep(1)

    # Start taking readings and publishing them at the specified interval
    next_sample_time = time.time()
    next_publish_time = time.time() + args["interval"]

    try:
        while True:
            if publisher.connection_error is not None:
                sys.exit(f"Connecting to the MQTT server failed: {publisher.connection_error}")
            
            should_publish = time.time() >= next_publish_time
            if should_publish:
                next_publish_time += args["interval"]
            
            acquire.update()

            if should_publish:
                for sensor_name in acquire.samples[0].keys():
                    value_sum = sum([d[sensor_name] for d in acquire.samples])
                    value_avg = value_sum / len(acquire.samples)
                    value = SensorPayload(
                        value=value_avg
                    )
                    topic = discovery.sensors[sensor_name].state_topic
                    publisher.publish_json(topic, value, retain=args['retain_state'])

            next_sample_time += 1
            sleep_duration = max(next_sample_time - time.time(), 0)
            time.sleep(sleep_duration)
    
    finally:
        publisher.destroy()


if __name__ == "__main__":
    main()
