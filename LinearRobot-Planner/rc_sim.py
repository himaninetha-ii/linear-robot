import paho.mqtt.client as mqtt
import time
import json
from dataclasses import dataclass
from typing import Optional, Any

@dataclass
class Event:
    eid: int
    ts: str
    ueid: str
    eg: Optional[str] = None
    ec: Optional[int] = None
    pl: Optional[dict[str, Any]] = None

def on_connect(client, userdata, flags, rc):
    client.subscribe("LinearRobotPlanner/event")
    print("Connected with result code", rc)

def on_message(client, userdata, msg):
    print("hi")
    message = Event(**json.loads(msg.payload.decode()))
    print(message)
    time.sleep(1)
    response={'eg': message.eg,'eid': message.eid,'ueid': message.ueid, 'ts': message.ts, "rc": 1,'pl': None}
    client.publish("LinearRobotRC/response", json.dumps(response))
    print(response)

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect("localhost", 1883)

client.loop_forever()
