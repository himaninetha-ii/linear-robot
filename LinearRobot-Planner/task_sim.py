import paho.mqtt.client as mqtt
import time
import json
import uuid
from datetime import datetime,timezone,timedelta

BROKER = "localhost"
TOPIC = "LinearRobotTask/event"
LOC_TOPIC = "LinearRobotHAL/telemetry"


IST = timezone(timedelta(hours=5, minutes=30))
TaskUUID=str(uuid.uuid4())
json_msg={
    'eg': 'LinearRobot',
    'eid': 10023,
    'ts': datetime.now(IST).isoformat(),
    'ueid': str(uuid.uuid4()),
    'ec': None,
    'pl': {"location":{"x":500,"y":500,"z":300},
    "action_type": "accurate_place"}
}

# json_msg={
#     'eg': 'LinearRobot',
#     'eid': 10022,
#     'ts': datetime.now(IST).isoformat(),
#     'ueid': str(uuid.uuid4()),
#     'ec': None,
#     'pl': {"location":{"x":600,"y":200,"z":80},
#     "action_type": "vision_pick"}
# }

# json_msg={
#     'eg': 'LinearRobot',
#     'eid': 10023,
#     'ts': datetime.now(IST).isoformat(),
#     'ueid': str(uuid.uuid4()),
#     'ec': None,
#     'pl': {"location":{"x":375,"y":1010,"z":40},
#     "action_type": "accurate_place"}
# }

client = mqtt.Client()
client.connect(BROKER, 1883)

# Start background loop so messages are sent immediately
client.loop_start()

# msg=json.dumps(json_msg)
pose_msg={
                                    'eg': 'LinearRobotTelemetry',
                                    'eid': 10010,
                                    'ts': datetime.now(IST).isoformat(),
                                    'ueid': str(uuid.uuid4()),
                                    'rc': 1,
                                    'pl': {'location':
                                        {'x': 600,
                                        'y':420,
                                        'z': 300,
                                        'c': 0  
                                        }
                                    }
                                }
# # Publish with retain so new subscribers also get it
# # result = client.publish(TOPIC, "G92 X0 Y0 Z0 C0", qos=1, retain=False)
# # result = client.publish(TOPIC, "G1 F1000 X0 Y0 Z0 C0", qos=1, retain=False)
client.publish(LOC_TOPIC, json.dumps(pose_msg), qos=1, retain=False)

# result = client.publish(TOPIC, msg, qos=1, retain=False)

# Wait until message is sent
# result.wait_for_publish()

# print("Published: M63 P0")

time.sleep(1)
client.loop_stop()
client.disconnect()
