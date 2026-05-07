import pyudev
import serial
import serial.tools.list_ports
import time
from datetime import datetime,timezone,timedelta
import threading
import json
import uuid

RESPONSE_TOPIC = "LinearRobotHAL/response"

class SerialTracker:

    def __init__(self,parent,TARGET_VENDOR,TARGET_PRODUCT,mqtt_client):
        self.TARGET_VENDOR=TARGET_VENDOR
        self.TARGET_PRODUCT=TARGET_PRODUCT
        self.client=mqtt_client
        self.state_topic="fluidnc/state"
        self.position_topic="LinearRobotHAL/telemetry"
        self.context=pyudev.Context()
        self.monitor=pyudev.Monitor.from_netlink(self.context)
        self.monitor.filter_by(subsystem='ttyUSB')
        # threading.Thread(target=self.monitor_udev, args=(lambda a, d: print(f"[{a}] {d}"),), daemon=True).start()
        # Start the main serial communication loop
        self.ser = None
        self.parent=parent

            

    def find_target_port(self):
        """Return device path (/dev/ttyUSB0) for target USB serial device."""
        for port in serial.tools.list_ports.comports():
            if port.vid and port.pid:
                if f"{port.vid:04x}" == self.TARGET_VENDOR and f"{port.pid:04x}" == self.TARGET_PRODUCT:
                    print(f"Found target device at {port.device}")
                    return port.device
        return None

    def monitor_udev(self,callback):
        """Thread to monitor plug/unplug events"""
        for action, device in self.monitor:
            if device.device_node:
                callback(action, device.device_node)

    def serial_worker(self):
        """Main serial communication loop"""
        
        self.port = self.find_target_port()
        
        while True:
            if port and self.ser is None:
                try:
                    self.restart_confirmed=True
                    self.ser = serial.Serial(port, 115200, timeout=1)
                    print(f"Connected to {port}")
                    self.read_startup_banner()
                except Exception as e:
                    print(f"Failed to open {port}: {e}")
                    self.ser = None
                    # time.sleep(1)
                    continue

            # if self.ser:
            #     try:
                    
            #         # self.ser.write(b'?')
            #         self.line = self.ser.readline().decode(errors='ignore').strip()
            #         if self.line:
                        
            #             try:
            #                 if self.line.startswith("<") and self.line.endswith(">"):
            #                     print(f"↩  Received: {self.line}")
            #                     self.line=self.line.strip("<>").split("|")
            #                     state=self.line[0]
            #                     mpos_part = next((p for p in self.line if p.startswith("MPos:")), None)
            #                     if mpos_part:
            #                         mpos = [float(x) for x in mpos_part.replace("MPos:", "").split(",")]
            #                     else:
            #                         mpos = []
            #                     # print(f"State: {state}, MPos: {mpos}")
            #                     self.client.publish(self.state_topic, state)
            #                     self.client.publish(self.position_topic, json.dumps(mpos))

            #             except Exception as e:
            #                 pass
                        
            #         else:
            #             print("No response, maybe disconnected?")
            #         time.sleep(0.1)

            #     except serial.SerialException as e:
            #         print(f"Serial error: {e}")
            #         self.ser.close()
            #         self.ser = None
            #         self.port = None
            #     except Exception as e:
            #         print(f"Unexpected error: {e}")
            #         time.sleep(1)

            if self.ser is None:
                # wait until port reappears
                new_port = self.find_target_port()
                if new_port:
                    port = new_port
                    print(f"Found port again: {port}")
                    

                else:
                    print("Waiting for device...")
                # self.check_for_restart()
                # if self.is_restarted:
                #     self.wait_for_wpos_correction()
                # time.sleep(2)

    # def check_for_restart(self):

    def read_startup_banner(self):
        """Read all startup messages from FluidNC right after connection."""
        print("📡 Waiting for FluidNC startup messages...")
        start = time.time()
        banner_lines = []
        while time.time() - start < 2.0:  # 2 seconds window
            if self.ser.in_waiting:
                line = self.ser.readline().decode(errors='ignore').strip()
                if line:
                    banner_lines.append(line)
                    print(f"{line}")
        # detect restart by startup keywords
        if any("[MSG:RST]" in l for l in banner_lines):
            print("FluidNC startup detected — board restarted!")
            self.restart_correction()
            self.restart_confirmed=True

    def restart_correction(self):
        """Wait until a valid WPos is received"""
        print("WPOS Correction")
        IST = timezone(timedelta(hours=5, minutes=30))
        restart_msg={'et': "LinearRobotEvent",'eid':10020,'ueid': str(uuid.uuid4), 'ts': datetime.now(IST).isoformat(), "ec": None,'pl': None}
        self.client.publish(RESPONSE_TOPIC,restart_msg)
        # while True:
        #     if self.ser:
        #         try:
        #             self.ser.write(b'?')
        #             line = self.ser.readline().decode(errors='ignore').strip()
        #             if line.startswith("<") and line.endswith(">"):
        #                 parts = line.strip("<>").split("|")
        #                 wpos_part = next((p for p in parts if p.startswith("WPos:")), None)
        #                 if wpos_part:
        #                     wpos = [float(x) for x in wpos_part.replace("WPos:", "").split(",")]
        #                     if all(coord != 0.0 for coord in wpos):
        #                         print(f"Valid WPos received: {wpos}")
        #                         return
        #             time.sleep(0.5)
        #         except Exception as e:
        #             print(f"Error while waiting for WPos: {e}")
        #             time.sleep(1)
        #     else:
        #         time.sleep(1)

    def send_ping(self):

        if self.ser:
                try:
                    self.ser.write('?')
                    # self.ser.write(b'?')
                    self.line = self.ser.readline().decode(errors='ignore').strip()
                    if self.line:
                        
                        try:
                            if self.line.startswith("<") and self.line.endswith(">"):
                                print(f"↩  Received: {self.line}")
                                self.line=self.line.strip("<>").split("|")
                                state=self.line[0]
                                mpos_part = next((p for p in self.line if p.startswith("MPos:")), None)
                                if mpos_part:
                                    mpos = [float(x) for x in mpos_part.replace("MPos:", "").split(",")]
                                else:
                                    mpos = []
                                wpos_part = next((p for p in self.line if p.startswith("WPos:")), None)
                                if wpos_part:
                                    wpos = [float(x) for x in wpos_part.replace("WPos:", "").split(",")]
                                else:
                                    wpos = last_wpos
                                last_wpos=wpos

                                # print(f"State: {state}, MPos: {mpos}")
                                pose=mpos-wpos
                                pose_msg={
                                    'et': 'LinearRobotTelemetry',
                                    'eid': 10010,
                                    'ts': self.parent.event.ts,
                                    'ueid': self.parent.event.ueid,
                                    'rc': None,
                                    'pl': {
                                        'x': pose[0],
                                        'y': pose[1],
                                        'z': pose[2],
                                        'c': pose[6]   
                                    }
                                }

                                self.client.publish(self.state_topic, state)

                                self.client.publish(self.position_topic, json.dumps(pose_msg))

                        except Exception as e:
                            pass
                        
                    else:
                        print("No response, maybe disconnected?")
                    time.sleep(0.1)

                except serial.SerialException as e:
                    print(f"Serial error: {e}")
                    self.ser.close()
                    self.ser = None
                    self.port = None
                except Exception as e:
                    print(f"Unexpected error: {e}")
                    time.sleep(1)
        
