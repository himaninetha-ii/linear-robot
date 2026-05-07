"""Configuration constants for the robot controller."""
from datetime import timezone, timedelta

# MQTT Configuration
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_KEEPALIVE = 60

# MQTT Topics
TOPIC_PLANNER_EVENT = "LinearRobotPlanner/event"
TOPIC_HAL_RESPONSE = "LinearRobotHAL/response"
TOPIC_HAL_TELEMETRY = "LinearRobotHAL/telemetry"
TOPIC_RC_HALCOMM = "LinearRobotRC/halcomm"
TOPIC_RC_RESTART = "LinearRobotRC/restart_event"
TOPIC_RC_RESPONSE= "LinearRobotRC/response"

# Timezone
IST = timezone(timedelta(hours=5, minutes=30))

# Command processing delay
COMMAND_PROCESS_DELAY = 0.1  # seconds