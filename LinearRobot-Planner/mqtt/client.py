"""
MQTT client management and message handling
"""
import json
from paho.mqtt.client import Client

from models.events import Event, Response
from models.enums import TaskID
from config.constants import (
    TOPIC_TASK_EVENT, TOPIC_RC_RESPONSE, 
    TOPIC_HAL_TELEMETRY, TOPIC_VISION_RESPONSE,
    MQTT_BROKER, MQTT_PORT, TOPIC_RC_RESTART_EVENT,
    TOPIC_PLANNER_RESET
)


class MQTTHandler:
    """Handle MQTT communication"""
    
    def __init__(self, blackboard, on_task_callback,parent):
        self.bb = blackboard
        self.on_task_callback = on_task_callback
        self.client = Client()
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.parent=parent

    def connect(self):
        """Connect to MQTT broker"""
        self.client.connect(MQTT_BROKER, MQTT_PORT)
        self.client.loop_start()

    def _on_connect(self, client, userdata, flags, rc):
        """Handle connection to MQTT broker"""
        print(f"Connected to MQTT broker with result code {rc}")
        client.subscribe(TOPIC_TASK_EVENT)
        client.subscribe(TOPIC_RC_RESPONSE)
        client.subscribe(TOPIC_HAL_TELEMETRY)
        client.subscribe(TOPIC_VISION_RESPONSE)
        client.subscribe(TOPIC_RC_RESTART_EVENT)
        client.subscribe(TOPIC_PLANNER_RESET)

    def _on_message(self, client, userdata, msg):
        """Handle incoming MQTT messages"""
        
        
        if msg.topic == TOPIC_TASK_EVENT:
            print(f"{msg.topic}: {msg.payload}")
            self._handle_task_event(msg)
        elif msg.topic == TOPIC_RC_RESPONSE:
            print(f"{msg.topic}: {msg.payload}")
            self._handle_rc_response(msg)
        elif msg.topic == TOPIC_HAL_TELEMETRY:
            self._handle_telemetry(msg)
        elif msg.topic == TOPIC_VISION_RESPONSE:
            self._handle_vision_response(msg)
        elif msg.topic == TOPIC_PLANNER_RESET:
            self._handle_ui_reset(msg)
        elif msg.topic==TOPIC_RC_RESTART_EVENT:
            self.parent.build_tree()

    def _handle_task_event(self, msg):
        """Handle task event messages"""
        payload = json.loads(msg.payload.decode("utf-8"))
        event = Event(**payload)
        setattr(self.bb, 'event', event)
        
        # Call the task callback to process the event
        self.on_task_callback(event)

    def _handle_rc_response(self, msg):
        """Handle robot controller response messages"""
        rc_response_msg = Response(**json.loads(msg.payload.decode("utf-8")))
        
        if rc_response_msg.ueid == self.bb.current_action_ueid:
            rc_response = rc_response_msg.rc
            setattr(self.bb, "rc_response", rc_response)

    def _handle_telemetry(self, msg):
        """Handle telemetry messages"""
        telemetry_msg = Response(**json.loads(msg.payload.decode("utf-8")))
        # print(telemetry_msg)
        location = telemetry_msg.pl['location']
        # print(location)
        setattr(self.bb, "current_location", location)

    def _handle_vision_response(self, msg):
        """Handle vision system response messages"""
        vision_response_msg = Response(**json.loads(msg.payload.decode("utf-8")))
        print(vision_response_msg)
        if (vision_response_msg.pl["trigger_ueid"] == self.bb.vision_trigger_ueid):
            setattr(self.bb, "vision_response_msg", vision_response_msg)

    def _handle_ui_reset(self,msg):
        self.parent.build_tree()