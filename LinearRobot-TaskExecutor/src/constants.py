"""Constants used across the application"""
from datetime import timezone, timedelta

# Timezone configuration
IST = timezone(timedelta(hours=5, minutes=30))

# API Base URL
# API_BASE_URL = "http://192.168.2.230:3000/api"
API_BASE_URL = "http://localhost:3001/api"

# MQTT Configuration
MQTT_BROKER_HOST = "localhost"
MQTT_BROKER_PORT = 1883

# MQTT Topics
TOPIC_RESPONSE = "LinearRobotPlanner/response"
TOPIC_EVENT = "LinearRobotTask/event"
TOPIC_DISCLAIMER_RESPONSE = "LinearRobotUI/disclaimer_response"
TOPIC_UI_EVENT = "LinearRobotUI/event"
TOPIC_INCOMPLETE = "LinearRobotTask/incomplete"
TOPIC_DONE = "LinearRobotTask/done"
