"""Task Executor for robot operations"""
import json
import sqlite3
import threading
import time
import uuid
from datetime import datetime
from paho.mqtt.client import Client

from src.utils.config import fetch_config

from ..models import Box, Response
from ..utils import fetch_layout, fetch_config, fetch_program, push_config
from ..constants import (
    IST, 
    MQTT_BROKER_HOST, 
    MQTT_BROKER_PORT,
    TOPIC_RESPONSE,
    TOPIC_EVENT,
    TOPIC_DISCLAIMER_RESPONSE,
    TOPIC_DONE
)


class TaskExecutor:
    """Handles robot task execution via MQTT commands"""
    
    def __init__(self, program_name: str) -> None:
        """
        Initialize the task executor.
        
        Args:
            program: The program to execute
        """
        self.program_name = program_name
        self.client = Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.response_topic = TOPIC_RESPONSE
        self.client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT)
        self.client.loop_start()
        self.event_topic = TOPIC_EVENT
        
        # Fetch initial layout
        self.program = fetch_program(program_name)
        self.layoutStack=self.program['layoutStack']
        self.misc=self.program['misc']
        self.preprocess_misc()

        
        
        self.received = False
        self.response_cv = threading.Condition()
        self.process = None
        self.conn = None
        self.cur = None

    def on_connect(self, client, userdata, flags, rc):
        """
        Callback for MQTT connection.
        
        Args:
            client: MQTT client instance
            userdata: User data
            flags: Connection flags
            rc: Result code
        """
        print(f"Connected to MQTT broker with result code {rc}") 
        client.subscribe(self.response_topic)
        client.subscribe(TOPIC_DISCLAIMER_RESPONSE)

    def on_message(self, client, userdata, msg):
        """
        Callback for MQTT message reception.
        
        Args:
            client: MQTT client instance
            userdata: User data
            msg: Received message
        """
        if msg.topic == self.response_topic:
            response_msg = Response(**json.loads(msg.payload.decode()))
            print(response_msg)
            if response_msg.ueid == self.current_ueid:
                with self.response_cv:
                    self.response_cv.notify_all()
        elif msg.topic == TOPIC_DISCLAIMER_RESPONSE:
            print(msg.payload.decode())
            response = Response(**json.loads(msg.payload.decode()))
           
            if response.pl['response'] == 'start_new_process':
                self.process = None
                self.received = True
                
            elif response.pl['response'] == 'continue_process':
                self.received = True
                layout = response.pl['layout_id']
                self.place_positions = fetch_layout(layout)

    def preprocess_misc(self):
        self.misc_layer_before = []
        self.misc_layer_after = []
        self.misc_box_before = []
        self.misc_box_after = []
        for action in self.misc:
            if action['interval'] == 'layer':
                if action['timeOfAction'] == 'before':
                    self.misc_layer_before.append(action['name'])
                elif action['timeOfAction'] == 'after':
                    self.misc_layer_after.append(action['name'])
            elif action['interval'] == 'box':
                if action['timeOfAction'] == 'before':
                    self.misc_box_before.append(action['name'])
                elif action['timeOfAction'] == 'after':
                    self.misc_box_after.append(action['name'])
        
    def start(self):
        """Start the task execution process"""
        if self.process != None:
            box_order = int(self.process[1])
            layout_order = int(self.process[2])
        else:
            box_order = 0
            layout_order = 0
            self.cur.execute("DELETE FROM current_process")
            self.cur.execute(
                "INSERT INTO current_process (program, placement_order, layout_order, last_updated) VALUES (?,?,?,?)",
                (self.program_name, 0, layout_order, datetime.now(IST).isoformat())
            )
            self.conn.commit()
        
        # Fetch initial corner position
        initial_corner = json.loads(fetch_config('initial_corner'))
        last_layout_height = json.loads(fetch_config('pallet_height'))*1000
        for index,layout_name in enumerate(self.layoutStack):
            if index < layout_order:
                continue
            layout_order = index
            layout = fetch_layout(layout_name)
            self.cur.execute(
                "UPDATE current_process SET layout_order = ? where program=?",
                (layout_order, self.program_name)
            )
            self.conn.commit()
            self.update_parameters(layout['parameters'])
            
            for layer in layout['data']['layers']:
                if self.misc_layer_before != []:
                    for action in self.misc_layer_before:
                        print(action)
                
                for box in layer:
                    if self.misc_box_before != []:
                        for action in self.misc_box_before:
                            print(action)
                    if box['placement_order'] < box_order:
                        continue
                    self.cur.execute(
                        "UPDATE current_process SET placement_order = ? where program=?",
                        (box['placement_order'], self.program_name)
                    )
                    self.conn.commit()
                    self.pick()
                    box = Box(**box)
                    
                    place_location = box.position
                    last_box_height=place_location[2]
                    place_location = [
                        place_location[0] + initial_corner['x'],
                        place_location[1] + initial_corner['y'],
                        place_location[2] + initial_corner['z'] + last_layout_height
                    ]
                    orientation = box.rotation
                    self.place(place_location)
                    if self.misc_box_after != []:
                        for action in self.misc_box_after:
                            print(action)
                last_layout_height += last_box_height
                print(last_layout_height)
                if self.misc_layer_after != []:
                    for action in self.misc_layer_after:
                        print(action)
        
        self.cur.execute("DELETE FROM current_process")
        self.conn.commit()
        result = self.client.publish(TOPIC_DONE, json.dumps({}))
        result.wait_for_publish()
        self.client.disconnect()

    def update_parameters(self, parameters):
        """
        Update parameters.
        
        Args:
            parameters: Dictionary containing parameters
        """
        for key, value in parameters.items():
            push_config(key, value)

    def pick(self):
        """Execute pick operation at configured pickup location"""
        pickup_loc = json.loads(fetch_config('pickup_location'))
        
        json_msg = {
            'eg': 'LinearRobot',
            'eid': 10022,
            'ts': datetime.now(IST).isoformat(),
            'ueid': str(uuid.uuid4()),
            'ec': None,
            'pl': {
                "location": {"x": pickup_loc['x'], "y": pickup_loc['y'], "z": pickup_loc['z']},
                "action_type": fetch_config('pick_type')
            }
        }
        self.send_message(json_msg)

    def place(self, place_location):
        """
        Execute place operation at specified location.
        
        Args:
            place_location: List of [x, y, z] coordinates
        """
        json_msg = {
            'eg': 'LinearRobot',
            'eid': 10023,
            'ts': datetime.now(IST).isoformat(),
            'ueid': str(uuid.uuid4()),
            'ec': None,
            'pl': {
                "location": {
                    "x": place_location[0],
                    "y": place_location[1],
                    "z": place_location[2]
                },
                "action_type": fetch_config('place_type')
            }
        }
        self.send_message(json_msg)

    def send_message(self, json_msg):
        """
        Send MQTT message and wait for response.
        
        Args:
            json_msg: Message dictionary to send
        """
        self.client.publish(self.event_topic, json.dumps(json_msg))
        self.current_ueid = json_msg['ueid']
        with self.response_cv:
            self.response_cv.wait()

    def verify_task_completion(self):
        """Check if there's an incomplete task and publish status"""
        with sqlite3.connect("task.db") as self.conn:
            self.cur = self.conn.cursor()
            self.cur.execute("""
            CREATE TABLE IF NOT EXISTS current_process (
                program INTEGER NOT NULL,
                placement_order TEXT NOT NULL,
                layout_order TEXT NOT NULL,
                last_updated TEXT NOT NULL
            )
            """)
            self.cur.execute("SELECT 1 FROM current_process LIMIT 1")
            process_incomplete = (self.cur.fetchone() is not None)
        
        if process_incomplete:
            self.cur.execute("SELECT * FROM current_process LIMIT 1") 
            self.process = self.cur.fetchone() 
            self.client.publish("LinearRobotTask/incomplete", json.dumps(self.process))
        else:
            self.process = None
            self.received = True
