"""Main robot controller handling MQTT communication and command processing."""
import json
import queue
import threading
import time
from datetime import datetime

from paho.mqtt.client import Client

from config.constants import (
    MQTT_BROKER, MQTT_PORT, MQTT_KEEPALIVE, IST,
    TOPIC_PLANNER_EVENT, TOPIC_HAL_RESPONSE, TOPIC_HAL_TELEMETRY,
    TOPIC_RC_HALCOMM, TOPIC_RC_RESPONSE, TOPIC_RC_RESTART, COMMAND_PROCESS_DELAY,
    TOPIC_RC_RESPONSE
)
from models.events import Event, Response
from models.enums import EventGroupID, EventID
from planner_sim import publish_event
from states.motion_state import MotionState
from states.gripper_state import GripperState


class RobotController:
    """Main controller for the linear robot system."""

    def __init__(self):
        # Initialize state machines
        self.motion = MotionState(self)
        self.gripper = GripperState(self)
        
        # Command tracking
        self.command_q = queue.Queue()
        self.priority_q = queue.Queue()
        self.ueid_dict = {}
        self.current_event_ueid = None
        
        # Motion parameters
        self.target = None
        self.feedrate = None
        
        # Initialize MQTT client
        self.client = Client()
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.paused=False
        
        # Connect and start
        self.client.connect(MQTT_BROKER, MQTT_PORT, MQTT_KEEPALIVE)
        self._start_command_processor()
        # self.send_ping()

    def _on_connect(self, client, userdata, flags, rc):
        """Handle MQTT connection."""
        print(f"Connected with result code {rc}")
        client.subscribe(TOPIC_PLANNER_EVENT)
        client.subscribe(TOPIC_HAL_RESPONSE)
        # client.subscribe(TOPIC_HAL_TELEMETRY)

    def _on_message(self, client, userdata, msg):
        """Handle incoming MQTT messages."""
        # print(repr(msg.payload))
        payload = json.loads(msg.payload.decode())
        
        if msg.topic == TOPIC_PLANNER_EVENT:
            self._handle_planner_event(payload)
        elif msg.topic == TOPIC_HAL_RESPONSE:
            self._handle_hal_response(payload)
        elif msg.topic == TOPIC_HAL_TELEMETRY:
            self._handle_hal_telemetry(payload)

    def _handle_planner_event(self, payload):
        """Process events from the planner."""
        event = Event(**payload)
        if event.eid==EventID.RESET:
            self.command_q=queue.Queue()
            self.priority_q=queue.Queue()
            self.gripper.state='off'
            self.ueid_dict={}
            self.paused=False
        # Priority commands
        priority_events = [
            EventID.PAUSE, EventID.RESUME, EventID.RESET,
            EventID.SERVO_ON, EventID.SERVO_OFF
        ]
        
        # Regular commands
        regular_events = [
            EventID.MOVE, EventID.GRIPPER_ON, EventID.GRIPPER_OFF
        ]
        
        if event.eid in priority_events:
            self._add_to_queue(event, is_priority=True)
        elif event.eid in regular_events:
            self._add_to_queue(event, is_priority=False)

    def _handle_hal_response(self, payload):
        """Process responses from the HAL."""
        print("Received HAL response:", payload)
        try:
            response = Response(**payload)

        except TypeError:
            event=Event(**payload)
        # Handle restart
            if event .eid == EventID.RESTART:
                print("HAL Restarted, resetting controller state")
                self.client.publish(TOPIC_RC_RESTART, "")
                # self.motion.machine.set_state('disabled')
                # self.gripper.machine.set_state('off')
                return
        
        if response.ueid!=self.current_event_ueid:
            while self.paused==True:
                time.sleep(0.5)
        # Process successful response
        if response.rc == 1 and self.current_event_ueid == response.ueid:
            self.publish_response(self.create_response(response.eg,response.eid,response.rc))
            self._complete_command(response.ueid)

    def _handle_hal_telemetry(self, payload):
        """Process telemetry from the HAL."""
        print("Received HAL telemetry:", payload)
        # Can be extended to store location in database

    def _add_to_queue(self, event, is_priority=False):
        """Add event to appropriate queue."""
        self.ueid_dict[event.ueid] = event
        if is_priority:
            self.priority_q.put(event)
        else:
            self.command_q.put(event)

    def _complete_command(self, ueid):
        """Mark command as completed."""
        if ueid in self.ueid_dict:
            self.motion.machine.set_state('enabled')
            del self.ueid_dict[ueid]
            print(f"Command {ueid} completed")
            if self.event.eid in [10007]:
                self.current_event_ueid=self.previous_event_ueid
                self.paused=False

    def _start_command_processor(self):
        """Start background thread for command processing."""
        thread = threading.Thread(target=self._process_commands, daemon=True)
        thread.start()

    def _process_commands(self):
        """Continuously process commands from queues."""
        while True:
            time.sleep(COMMAND_PROCESS_DELAY)
            # Priority commands first
            if not self.priority_q.empty():
                self._execute_priority_command()
                
            # Regular commands when no active event
            elif self.ueid_dict and self.current_event_ueid not in self.ueid_dict and not self.command_q.empty():
                self._execute_regular_command()

    def _execute_priority_command(self):
        """Execute a priority command."""
        self.event = self.priority_q.get()
        if self.event.eid in [10006]:
            self.paused=True
            self.previous_event_ueid=self.current_event_ueid
        self.current_event_ueid = self.event.ueid
        
        command_map = {
            EventID.PAUSE: self.motion.pause,
            EventID.RESUME: self.motion.resume,
            EventID.RESET: self.motion.home,
            EventID.SERVO_ON: self.motion.enable,
            EventID.SERVO_OFF: self.motion.disable,
        }
        
        handler = command_map.get(self.event.eid)
        if handler:
            handler()
        
        self.priority_q.task_done()
        

    def _execute_regular_command(self):
        """Execute a regular command."""
        while self.paused:
                return
        self.event = self.command_q.get()
        
        if self.motion.state=="disabled":
            self.motion.enable()
        self.current_event_ueid = self.event.ueid
        
        if self.event.eid == EventID.MOVE:
            
            self.target = self.event.pl.get('location', {})
            self.feedrate = self.event.pl.get('feedrate', 0)
            self.motion.move()
            
        elif self.event.eid == EventID.GRIPPER_ON:
            if self.gripper.state == 'off':
                self.gripper.turn_on()
            else:
                self.publish_response(self.create_response(self.event.eg,self.event.eid,1))
                self._complete_command(self.current_event_ueid)
                
        elif self.event.eid == EventID.GRIPPER_OFF:
            if self.gripper.state == 'on':
                self.gripper.turn_off()
            else:
                self.publish_response(self.create_response(self.event.eg,self.event.eid,1))
                self._complete_command(self.current_event_ueid)
        else:
            print(f"Unknown command: {self.event.eid}")
        
        self.command_q.task_done()

    def create_message(self, event_group, event_id, payload=None):
        """Create a standardized event message."""
        return {
            'eg': event_group,
            'eid': event_id,
            'ueid': self.current_event_ueid,
            'ts': datetime.now(IST).isoformat(),
            'ec': None,
            'pl': payload
        }
    
    def create_response(self, event_group, event_id, response,payload=None):
        """Create a standardized event message."""
        return {
            'eg': event_group,
            'eid': event_id,
            'ueid': self.current_event_ueid,
            'ts': datetime.now(IST).isoformat(),
            'rc': response,
            'pl': payload
        }

    def publish_event(self, message):
        """Publish event to HAL."""
        self.client.publish(TOPIC_RC_HALCOMM, json.dumps(message))
        print(message)

    def publish_response(self,response):
        """Publish response to Planner"""
        self.client.publish(TOPIC_RC_RESPONSE,json.dumps(response))
    def get_states(self):
        """Get current state of all subsystems."""
        return {
            'motion_state': self.motion.state,
            'gripper_state': self.gripper.state,
        }

    def run(self):
        """Start the controller's main loop."""
        self.client.loop_forever()

    def send_ping(self):
        msg=self.create_message(EventGroupID.LINEAR_ROBOT,EventID.PING)
        self.publish_event(msg)
        