"""MQTT Trigger for starting main program"""
import json
import subprocess
import sys
import threading
from paho.mqtt.client import Client

from ..models import Event, EventID
from ..constants import MQTT_BROKER_HOST, MQTT_BROKER_PORT, TOPIC_UI_EVENT


class MQTTTrigger:
    """MQTT client that listens for start signals and launches main.py"""
    
    def __init__(self, broker_host=MQTT_BROKER_HOST, broker_port=MQTT_BROKER_PORT):
        """
        Initialize MQTT client to trigger main.py execution
        
        Args:
            broker_host: MQTT broker hostname (default: localhost)
            broker_port: MQTT broker port (default: 1883)
        """
        self.broker_host = broker_host
        self.broker_port = broker_port
        
        self.main_process = None
        
        # Initialize MQTT client
        self.client = Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        
    def on_connect(self, client, userdata, flags, rc):
        """Callback when connected to MQTT broker"""
        if rc == 0:
            print(f"✓ Connected to MQTT broker at {self.broker_host}:{self.broker_port}")
            client.subscribe(TOPIC_UI_EVENT)
            
            print(f"✓ Subscribed to topic: {TOPIC_UI_EVENT}")
        else:
            print(f"✗ Failed to connect to MQTT broker, return code: {rc}")
    
    def on_message(self, client, userdata, msg):
        """Callback when message is received on subscribed topic"""
        try:
            payload = msg.payload.decode()
            event = Event(**json.loads(payload))
            print(f"\n📨 Received message on topic '{msg.topic}': {payload}")
            
            if event.eid == EventID.START:
                self.start_main(event)
            elif event.eid == EventID.RESET:
                if self.main_process:
                    self.main_process.terminate()
            
        except Exception as e:
            print(f"✗ Error processing message: {e}")
    
    def start_main(self, event):
        """
        Start the main.py program
        
        Args:
            event: Event object containing layout information
        """
        try:
            print("🚀 Starting main.py...")
            print(event)
            # Start the process without capturing output - let it print directly
            self.main_process = subprocess.Popen(
                [sys.executable, "main.py", '--program', event.pl['programName']],
                stdout=None,  # Inherit parent's stdout
                stderr=None,  # Inherit parent's stderr
            )
            print(f"✓ main.py started with PID: {self.main_process.pid}")
            
            # Monitor the process in a separate thread
            def monitor_process():
                """Monitor the subprocess and handle completion"""
                exit_code = self.main_process.wait()
                if exit_code != 0:
                    print(f"\n⚠️  main.py exited with error code: {exit_code}")
                else:
                    print(f"\n✓ main.py completed successfully")
                    self.main_process.terminate()
                    self.main_process.wait()
                    self.main_process = None
            
            monitor_thread = threading.Thread(target=monitor_process, daemon=True)
            monitor_thread.start()
            
        except Exception as e:
            print(f"✗ Failed to start main.py: {e}")
            import traceback
            traceback.print_exc()
    
    def run(self):
        """Connect to broker and start listening"""
        try:
            print(f"🔌 Connecting to MQTT broker at {self.broker_host}:{self.broker_port}...")
            self.client.connect(self.broker_host, self.broker_port)
            print("👂 Listening for start signals...")
            self.client.loop_forever()
        except KeyboardInterrupt:
            print("\n⏹️  Shutting down MQTT trigger...")
            self.cleanup()
        except Exception as e:
            print(f"✗ Error: {e}")
            self.cleanup()
    
    def cleanup(self):
        """Cleanup resources"""
        if self.main_process and self.main_process.poll() is None:
            print("Terminating main.py process...")
            self.main_process.terminate()
            self.main_process.wait()
        self.client.disconnect()
        print("✓ Cleanup complete")
