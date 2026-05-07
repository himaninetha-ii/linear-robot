from serial_tracker import SerialTracker
import threading
import paho.mqtt.client as mqtt
import time
import json
from datetime import datetime,timedelta,timezone
from enum import IntEnum

IST=timezone(timedelta(hours=5, minutes=30))

TARGET_VENDOR = "10c4"
TARGET_PRODUCT = "ea60"
GCODE_SUB_TOPIC = "linearPalletizer/send_gcode"
RESPONSE_PUB_TOPIC = "LinearRobotHAL/response"

class ResponseStatus(IntEnum):
    success=1
    failure=2

class GCodeSender:
    def __init__(self,client):
        self.client=client
        # self.client.connect('localhost',1883)
        # self.client.on_connect = self.on_connect
        # self.client.on_message = self.on_message
        # self.client.loop_start()
        self.serial_tracker=SerialTracker(self,TARGET_VENDOR, TARGET_PRODUCT,self.client)
        # self.receive_topic = "linearPalletizer/send_gcode"
        # self.response_topic = "linearPalletizer/gcode_response"

        threading.Thread(target=self.serial_tracker.serial_worker, daemon=True).start()
        time.sleep(1)

        self.queue = []
        self.lock = threading.Lock()
        self.worker = threading.Thread(target=self.process_queue, daemon=True)
        self.worker.start()

    

        


    def send_gcode(self, line):
        response=False
        line = line.strip()
        if not line or line.startswith(';') or line.startswith('('):
            return

        while self.serial_tracker.ser==None or self.serial_tracker.restart_confirmed:
            time.sleep(0.1)
        print(f">>> {line}")


        # Wait for response
        if line in ["!","~"]:
            try:
                with self.lock:
                    self.serial_tracker.ser.write((line + '\n').encode())
            except:
                while True:
                    if self.serial_tracker.ser:
                        self.serial_tracker.ser.write((line + '\n').encode())
            self.client.publish(RESPONSE_PUB_TOPIC, 'ok')
            
        elif line =="?":
            with self.lock:
                self.serial_tracker.send_ping()
        
        elif line == "G4 P0":
            try:
                with self.lock:
                    self.serial_tracker.ser.write((line + '\n').encode())
            except:
                while True:
                    if self.serial_tracker.ser:
                        self.serial_tracker.ser.write((line + '\n').encode())
            start_time=time.time()
            while True:
                # self.pause_event.wait()  # pause if needed
                end_time=time.time()
                response = self.serial_tracker.line
                if type(response)==str:
                    if 'ok' in response.lower() or 'error' in response.lower():
                        if response=='ok':
                            responsecode=ResponseStatus.success
                        elif response=='error':
                            responsecode=ResponseStatus.failure
                        response={'et': self.event.et,'eid':self.event.eid,'ueid': self.event.ueid, 'ts': datetime.now(IST).isoformat(), "rc": responsecode,'pl': self.event.pl}
                        self.client.publish(RESPONSE_PUB_TOPIC, json.dumps(response))
                        print(response)
                        break
                    time.sleep(0.1)
                if end_time-start_time>4:
                    self.serial_tracker.ser.write((line + '\n').encode())
                    start_time=time.time()

        else:
            self.serial_tracker.ser.write((line + '\n').encode())
            while True:
                # self.pause_event.wait()  # pause if needed
                response = self.serial_tracker.line
                
                if type(response)==str:
                    # print(response)
                    # self.client.publish(RESPONSE_PUB_TOPIC, response)
                    if 'ok' in response.lower() or 'error' in response.lower():
                        break

    def enqueue(self, line):
        with self.lock:
            self.queue.append(line)

    def process_queue(self):
        while True:
            if self.queue:
                with self.lock:
                    line = self.queue.pop(0)

                # Pause/resume handled inside send
                self.send_gcode(line)

                # After motion commands, send dwell
                if any(cmd in line.upper() for cmd in ['G0', 'G1', 'G2', 'G3', 'G4', 'M62', 'M63']):
                    time.sleep(0.3)
                    self.send_gcode("G4 P0")
            else:
                time.sleep(0.01)



    # def on_message(self,client, userdata, msg):
    #     message = msg.payload.decode().strip()
    def process_gcode(self,message,event):
        self.event=event    
        if message == "!":
            # self.pause_event.clear()
            self.send_gcode(message)
        
            # self.client.publish(RESPONSE_PUB_TOPIC, "Paused")
        elif message == ["~",'?']:
            # self.pause_event.set()
            self.send_gcode(message)
        
            # self.client.publish(RESPONSE_PUB_TOPIC, "Resumed")
        else:
            self.enqueue(message)
    

    
    
    
    