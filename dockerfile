# Use an official Python base image
FROM python:3.10-slim

# Set environment variables
ENV MQTT_BROKER="192.168.0.180" \
    MQTT_PORT=1883 \
    MQTT_TOPIC="sma/data" \
    MQTT_USERNAME="your_username" \
    MQTT_PASSWORD="your_password"

# Set the working directory
WORKDIR /app

# Copy the requirements file and the Python script
COPY requirements.txt .
COPY sma2mqtt.py .
COPY speedwiredecoder.py .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port for MQTT (optional, only if needed for debugging)
EXPOSE 1883

# Command to run your Python script
CMD ["python", "sma2mqtt.py"]
