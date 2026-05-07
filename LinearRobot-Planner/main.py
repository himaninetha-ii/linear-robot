"""
Main entry point for planner
"""
import py_trees
import time
import threading
import json
from models.enums import TaskID
from mqtt.client import MQTTHandler
from tree.builder import BehaviorTreeBuilder, calculate_locations, calculate_state_values

from datetime import datetime

from config.constants import IST



class Planner:
    def __init__(self):
        self.bb = py_trees.blackboard.Client(name="bb")
        self._init_blackboard()
        
        # Setup MQTT
        self.mqtt_handler = MQTTHandler(self.bb, self._handle_task_event,self)
        self.mqtt_handler.connect()
        
        # Register MQTT client in blackboard
        self.bb.register_key(key="client", access=py_trees.common.Access.WRITE)
        self.bb.client = self.mqtt_handler.client
        
        # Build behavior tree
        self.bt_complete_cv=threading.Condition()
        threading.Thread(target=self.reset_tree,daemon=True).start()

        tree_builder = BehaviorTreeBuilder(self.bb,self.bt_complete_cv)
        self.tree = tree_builder.build()

        self.bb.current_location={
            'x': 0,
            'y': 0,
            'z': 0,
            'c': 0
            }

    def build_tree(self):
        self.bb.current_task_ueid=None
        time.sleep(1)
        self.tree=BehaviorTreeBuilder(self.bb,self.bt_complete_cv).build()
        

    def reset_tree(self):
        while True:
            with self.bt_complete_cv:
                self.bt_complete_cv.wait()
                # self.tree.reset()
                # print("Rebuilding tree")
                self.tree=BehaviorTreeBuilder(self.bb,self.bt_complete_cv).build()
                # print("Tree rebuilt")

                self.publish_response()

    def publish_response(self):
        event=self.bb.event
        json_msg={
            'eg': event.eg,
            'eid': event.eid,
            'ts': datetime.now(IST).isoformat(),
            'ueid': event.ueid,
            'rc':1,
            'pl':{'location': self.bb.current_location}
        }
        self.mqtt_handler.client.publish("LinearRobotPlanner/response",json.dumps(json_msg))
        print(json_msg)
            

    def _init_blackboard(self):
        """Initialize blackboard variables"""
        variables = [
            "event", "rc_response", "vision_trigger_msg", "current_location",
            "action_location", "current_action", "current_action_type",
            "pick_circle_center", "pick_circle_radius", "place_circle_center",
            "place_circle_radius", "/location/intermediate", "/location/preaction",
            "/location/action", "/location/postaction", "/location/accurate_place/offset",
            "/location/accurate_place/down", "/location/accurate_place/offset_correction",
            "gripper_action", "current_task_ueid", "current_action_ueid",
            "vision_trigger_ueid", "vision_response_msg", "/location/vision_pick_intermediate"
        ]
        
        for variable in variables:
            self.bb.register_key(key=variable, access=py_trees.common.Access.WRITE)
            setattr(self.bb, variable, None)

    def _handle_task_event(self, event):
        """Handle incoming task events"""
        # Determine action type and location
        if event.eid == TaskID.PICK:
            action_location = "box"
            current_action = "pick"
        elif event.eid == TaskID.PLACE:
            action_location = "pallet"
            current_action = "place"
        else:
            print(f"Unknown task ID: {event.eid}")
            return
        
        
        self.bb.current_action_type=event.pl.get("action_type", "")
        # Calculate all locations
        locations = calculate_locations(event, self.bb,action_location)
        for key, value in locations.items():
            setattr(self.bb, key, value)
        
        # Calculate state values
        state_values = calculate_state_values(event, current_action)
        for key, value in state_values.items():
            setattr(self.bb, key, value)
        
        # Start behavior tree execution in separate thread
        thread = threading.Thread(target=self._tick_tree, daemon=True)
        thread.start()

    def _tick_tree(self):
        """Tick the behavior tree until task completion"""
        while self.bb.current_task_ueid is not None:
            time.sleep(0.1)
            self.tree.tick()

    def run(self):
        """Run planner"""
        print("Planner started")
        try:
            while True:
                time.sleep(3)
        except KeyboardInterrupt:
            print("\nShutting down Planner")


def main():
    """Main entry point"""
    planner = Planner()
    planner.run()


if __name__ == "__main__":
    main()