"""
Configuration constants for the robot control system
"""
from datetime import timedelta, timezone
import requests
import json

API="http://localhost:5173/api/config/"

class Configuration:
    def _get_config(self, key, default):
        try:
            response = requests.get(f"{API}{key}", timeout=0.5) # Short timeout for responsiveness
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict) and 'value' in data:
                    val = data['value']
                    if isinstance(default, int):
                        return int(val)
                    elif isinstance(default, float):
                        return float(val)
                    elif isinstance(default, dict):
                        if isinstance(val, str):
                            try:
                                return json.loads(val)
                            except:
                                return val
                        return val
                    return val
                return data
        except Exception as e:
            # print(f"Error fetching config for {key}: {e}") # Suppress print to avoid spamming logs
            pass
        return default

    # Location Constants
    @property
    def PICKUP_LOC(self): return self._get_config('pickup_location', {"x": 600, "y": 0, "z": 80})
    
    @property
    def INITIAL_CORNER(self): return self._get_config('initial_corner', {"x":175, "y": 420})
    

    # Dimension Constants
    @property
    def BOX_LENGTH(self): return self._get_config('box_length', 300)
    @property
    def BOX_WIDTH(self): return self._get_config('box_width', 300)
    @property
    def BOX_HEIGHT(self): return self._get_config('box_height', 150)
    @property
    def PALLET_LENGTH(self): return self._get_config('pallet_length', 610)
    @property
    def PALLET_WIDTH(self): return self._get_config('pallet_width', 610)
    @property
    def PALLET_HEIGHT(self): return self._get_config('pallet_height', 110)

    # Offset Constants
    @property
    def Z_OFFSET_PICK(self): return self._get_config('pick_z_offset', 400)
    @property
    def Z_OFFSET_PLACE(self): return self._get_config('place_z_offset', 200)
    @property
    def ACCURATE_PLACE_OFFSET(self): return self._get_config('accurate_placement_offset', 40)
    @property
    def INTERMEDIATE_POINT_TOLERANCE(self): return self._get_config('intermediate_placement_tolerance', 50)

    # Feedrate
    @property
    def MOVE_FEEDRATE(self): return self._get_config('move_feedrate', 30000)
    @property
    def VERTICAL_FEEDRATE(self): return self._get_config('vertical_feedrate', 20000)

Config = Configuration()

# Timezone
IST = timezone(timedelta(hours=5, minutes=30))

# MQTT Topics
TOPIC_TASK_EVENT = "LinearRobotTask/event"
TOPIC_RC_RESPONSE = "LinearRobotRC/response"
TOPIC_HAL_TELEMETRY = "LinearRobotHAL/telemetry"
TOPIC_VISION_RESPONSE = "LinearRobotVision/response"
TOPIC_PLANNER_EVENT = "LinearRobotPlanner/event"
TOPIC_VISION_EVENT = "LinearRobotVision/event"
TOPIC_RC_RESTART_EVENT="LinearRobotRC/restart_event"
TOPIC_PLANNER_RESET="LinearRobotPlanner/reset"

AVOIDANCE_CONSTANT=160

# MQTT Connection
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
