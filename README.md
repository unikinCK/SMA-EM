SMA Energy Meter Decoder and MQTT Publisher

This application decodes SMA Energy Meter data and publishes it to an MQTT broker, allowing seamless integration with Home Assistant or other IoT platforms. It supports MQTT discovery and is designed to provide accurate energy data for monitoring and analytics.

Features

Decodes SMA Energy Meter data packets.

Publishes decoded data to an MQTT broker.

Supports MQTT discovery for automatic integration with Home Assistant.

Configurable via environment variables.

Outputs energy metrics such as power consumption, supply, and energy counters.

Prerequisites

Python 3.8+

Required Python Libraries:

paho-mqtt

json

MQTT Broker: An active MQTT broker (e.g., Mosquitto).

SMA Energy Meter or Home Manager 2.0 connected to the local network.