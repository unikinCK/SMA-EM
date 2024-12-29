import json
import paho.mqtt.publish as publish

# Input file path
input_json_file = "sampledata.json"

# MQTT broker configuration
MQTT_BROKER = "192.168.0.180"  # Replace with your MQTT broker IP
MQTT_PORT = 1883
DISCOVERY_PREFIX = "homeassistant"
DEVICE_NAME = "SMA Energy Meter"
MANUFACTURER = "SMA"
MODEL = "Energy Meter"

# Load JSON data
with open(input_json_file, "r") as file:
    data = json.load(file)

# Generate MQTT discovery messages
messages = []
device_id = f"sma_{data['serial']}"

for key, value in data.items():
    # Skip unit keys, handled with corresponding sensor keys
    if key.endswith("unit"):
        continue

    # Determine unit of measurement (if available)
    unit_key = f"{key}unit"
    unit = data.get(unit_key, None)

    # Define discovery topic and payload
    discovery_topic = f"{DISCOVERY_PREFIX}/sensor/{device_id}/{key}/config"
    payload = {
        "name": key.capitalize(),
        "state_topic": f"sma/data/{data['serial']}/{key}",
        "unique_id": f"{device_id}_{key}",
        "device": {
            "identifiers": [device_id],
            "manufacturer": MANUFACTURER,
            "model": MODEL,
            "name": DEVICE_NAME,
        },
    }

    # Add attributes for energy counters
    if "counter" in key:  # Assuming energy counters contain "counter" in the key
        payload.update({
            "device_class": "energy",
            "state_class": "total_increasing",
            "unit_of_measurement": unit,
        })
    elif unit:
        payload["unit_of_measurement"] = unit

    # Add the payload to the messages list
    messages.append((discovery_topic, json.dumps(payload), 0, True))

# Publish all messages to MQTT broker
publish.multiple(messages, hostname=MQTT_BROKER, port=MQTT_PORT)

print("MQTT discovery messages sent to Home Assistant.")
