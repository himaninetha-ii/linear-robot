# fake_hal_responder.py
import paho.mqtt.client as mqtt
import json
from datetime import datetime, timezone, timedelta

IST = timezone(timedelta(hours=5, minutes=30))

client = mqtt.Client()
client.connect("localhost", 1883, 60)

def on_connect(client, userdata, flags, rc):
    print("HAL connected with result code", rc)
    client.subscribe("LinearRobotRC/halcomm")

def on_message(client, userdata, msg):
    payload = json.loads(msg.payload.decode())
    print(f"HAL received: {payload}")

    # Extract values safely
    eid = payload.get("eid")
    ueid = payload.get("ueid")

    # Simulate a small processing delay
    import time
    time.sleep(2)

    # Craft and send response back to controller
    response = {
        "eid": eid,
        "ueid": ueid,
        "ts": datetime.now(IST).isoformat(),
        "rc": 1
    }

    client.publish("LinearRobotHAL/response", json.dumps(response))
    print(f"HAL sent response: {response}")

client.on_connect = on_connect
client.on_message = on_message

print("Fake HAL running. Waiting for controller events...")
client.loop_forever()
