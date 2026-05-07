"""Configuration constants for the Linear Robot system."""

# Serial Device Configuration
TARGET_VENDOR = "10c4"
TARGET_PRODUCT = "ea60"

# MQTT Topics
EVENT_TOPIC = "LinearRobotRC/halcomm"
RESPONSE_PUB_TOPIC = "LinearRobotHAL/response"
# STATE_TOPIC = "fluidnc/state"
POSITION_TOPIC = "LinearRobotHAL/telemetry"

# MQTT Broker Configuration
MQTT_BROKER = "localhost"
MQTT_PORT = 1883

# Queue Configuration
MAX_QUEUE_SIZE = 10
QUEUE_PROCESS_DELAY = 0.02

# Serial Configuration
SERIAL_BAUD_RATE = 115200
INITIAL_SERIAL_TIMEOUT = 1
PROGRAM_SERIAL_TIMEOUT=1
STARTUP_BANNER_TIMEOUT = 2.0
COMMAND_TIMEOUT = 30.0


