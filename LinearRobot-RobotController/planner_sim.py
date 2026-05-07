# test_publisher.py
import paho.mqtt.client as mqtt
import json
import uuid
from datetime import datetime, timezone, timedelta
import time

IST = timezone(timedelta(hours=5, minutes=30))

client = mqtt.Client()
client.connect("localhost", 1883, 60)

def publish_event(topic, eid, payload=None):
    event = {
        "eid": eid,
        "ueid": str(uuid.uuid4()),
        "ts": datetime.now(IST).isoformat(),
        "pl": payload or {}
    }
    client.publish(topic, json.dumps(event))
    print(f"Published to {topic}: {event}")

# publish_event("LinearRobotPlanner/event", 10004)
# # Simulate a move command
# publish_event("LinearRobotPlanner/event", 10001, {"location": {"x": 10, "y": 5, "z": 2}, "feedrate": 1000})

# # Simulate a gripper on command
# publish_event("LinearRobotPlanner/event", 10002)
# time.sleep(5)
# # Simulate a pause command (priority)
# publish_event("LinearRobotPlanner/event", 10006)
# # time.sleep(3)
# publish_event("LinearRobotPlanner/event", 10007)

# client.loop(2)