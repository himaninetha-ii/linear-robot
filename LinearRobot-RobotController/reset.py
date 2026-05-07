import paho.mqtt.client as mqtt
import time
import json
import uuid
from datetime import datetime,timezone,timedelta

BROKER = "localhost"
TOPIC = "LinearRobotPlanner/event"


IST = timezone(timedelta(hours=5, minutes=30))

json_msg={
    'eg':  10000,
    'eid': 10001,
    'ts': datetime.now(IST).isoformat(),
    'ueid': str(uuid.uuid4()),
    'ec': 1,
    'pl': {
                "location": {'x': 500, 'y': 0, 'z':0,'c':0},
                "feedrate": 1000
            }
}

client = mqtt.Client()
client.connect(BROKER, 1883)

# Start background loop so messages are sent immediately
client.loop_start()

msg=json.dumps(json_msg)

# Publish with retain so new subscribers also get it
# result = client.publish(TOPIC, "G92 X0 Y0 Z0 C0", qos=1, retain=False)
# result = client.publish(TOPIC, "G1 F1000 X0 Y0 Z0 C0", qos=1, retain=False)
result = client.publish(TOPIC, msg, qos=1, retain=False)
# while True:
#     result = client.publish(TOPIC, msg, qos=1, retain=False)
#     result.wait_for_publish()
#     time.sleep(0.2)
# Wait until message is sent


# print("Published: M63 P0")

time.sleep(1)
client.loop_stop()
client.disconnect()