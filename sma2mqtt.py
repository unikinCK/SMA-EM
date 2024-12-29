#!/usr/bin/env python3
# coding=utf-8
"""
 *
 * Combined SMA Energy Meter Data Decoder and MQTT Publisher
 * Updated for MQTT by Christoph Kloberdanz
 *
 *  This software is released under GNU General Public License, version 2.
 *  See the GNU General Public License for more details.
 *
"""

import signal
import sys
import socket
import struct
import binascii
import json
import paho.mqtt.client as mqtt
import time
from speedwiredecoder import *

# MQTT Configuration
import os

# MQTT Configuration with environment variables
MQTT_BROKER = os.getenv("MQTT_BROKER", "192.168.0.180")  # Default to "127.0.0.1"
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))           # Default to 1883
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "sma/data")        # Default to "sma/data"
MQTT_USERNAME = os.getenv("MQTT_USERNAME", "your_username")  # Default to "your_username"
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "your_password")  # Default to "your_password"

# Initialize MQTT client
mqtt_client = mqtt.Client()
mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

try:
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.loop_start()
except Exception as e:
    print(f"Failed to connect to MQTT broker: {e}")
    sys.exit(1)

# Unit definitions with scaling
sma_units = {
    "W": 10,
    "VA": 10,
    "VAr": 10,
    "kWh": 3600000,
    "kVAh": 3600000,
    "kVArh": 3600000,
    "A": 1000,
    "V": 1000,
    "°": 1000,
    "Hz": 1000,
}

# Map of all defined SMA channels
sma_channels = {
    # ... channel definitions (same as provided earlier) ...
}

def decode_OBIS(obis):
    measurement = int.from_bytes(obis[0:2], byteorder='big')
    raw_type = int.from_bytes(obis[2:3], byteorder='big')
    if raw_type == 4:
        datatype = 'actual'
    elif raw_type == 8:
        datatype = 'counter'
    elif raw_type == 0 and measurement == 36864:
        datatype = 'version'
    else:
        datatype = 'unknown'
        print(f"Unknown datatype: measurement {measurement} datatype {datatype} raw_type {raw_type}")
    return measurement, datatype

def send_to_mqtt(data):
    try:
        mqtt_client.publish(MQTT_TOPIC, json.dumps(data))
        #print(f"Data sent to MQTT broker: {data}")
    except Exception as e:
        print(f"Failed to send data to MQTT broker: {e}")

# Clean exit
def abortprogram(signal, frame):
    print('SIGINT received, exiting program...')
    mqtt_client.loop_stop()
    mqtt_client.disconnect()
    sys.exit(0)

# Register signal handler
signal.signal(signal.SIGINT, abortprogram)

# Set up multicast socket
ipbind = '0.0.0.0'
MCAST_GRP = '239.12.255.254'
MCAST_PORT = 9522
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(('', MCAST_PORT))
try:
    mreq = struct.pack("4s4s", socket.inet_aton(MCAST_GRP), socket.inet_aton(ipbind))
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
except Exception as e:
    print(f"Could not connect to multicast group: {e}")
    sys.exit(1)

def send_to_mqtt(data):
    try:
        for key, value in data.items():
            # Publish all non-unit data normally
            topic = f"{MQTT_TOPIC}/{data['serial']}/{key}"
            mqtt_client.publish(topic, value)
            #print(f"Data sent to MQTT broker: {topic} -> {value}")
    except Exception as e:
        print(f"Failed to send data to MQTT broker: {e}")


# Publish units once before entering the main loop
topic = f"{MQTT_TOPIC}/Status/"
mqtt_client.publish(topic, "connected")

#create samplefile
datagram = sock.recv(608)
decoded_data = decode_speedwire(datagram)
# Filepath to save JSON data
file_path = "sampledata.json"
# Write JSON data to disk
with open(file_path, "w") as file:
    json.dump(decoded_data, file, indent=4)  # `indent` for pretty formatting

#publish autodiscover
import haautodiscover

# Main loop to process datagrams
while True:
    try:
        datagram = sock.recv(608)
        decoded_data = decode_speedwire(datagram)
        if decoded_data:
            send_to_mqtt(decoded_data)
    except Exception as e:
        print(f"Error processing datagram: {e}")

