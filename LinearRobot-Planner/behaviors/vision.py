"""
Vision-based picking behavior nodes
"""
import py_trees
import json
import uuid
from datetime import datetime

from config.constants import IST, Config
from models.enums import EventGroupID, EventID
import time

class VisionPick(py_trees.behaviour.Behaviour):
    """Perform vision-based object detection and picking"""
    
    def __init__(self, pick_name: str, blackboard):
        super().__init__(name=f'VisionPick{pick_name}')
        self.pick_name = pick_name
        self.bb = blackboard
        self.client = self.bb.client
        self.sent = False

    def update(self) -> py_trees.common.Status:
        if not self.sent:
            return self._trigger_vision()
        
        if self.bb.vision_response_msg is None:
            self.end_time=time.time()
            if ((self.end_time-self.start_time)>5.0):
                self.sent=False
                return py_trees.common.Status.FAILURE
            return py_trees.common.Status.RUNNING
        
        if self.bb.vision_response_msg.rc == 1:
            # input("Press Enter to continue")
            self._process_vision_result()
            return py_trees.common.Status.SUCCESS
        
        if self.bb.vision_response_msg.rc == 2:
            self.sent = False
            time.sleep(2)
            return py_trees.common.Status.FAILURE
            

    def _trigger_vision(self) -> py_trees.common.Status:
        """Trigger vision system"""
        # input("Press Enter to continue")
        time.sleep(0.5)
        print("Vision")
        
        self.bb.vision_response_msg = None
        
        vision_trigger_msg = {
            "eg": EventGroupID.VISION.value,
            "eid": EventID.VISION.value,
            "ts": datetime.now(IST).isoformat(),
            "ueid": str(uuid.uuid4()),
            "ec": None,
            "pl": {"location": self.bb.current_location}
        }
        
        self.bb.vision_trigger_ueid = vision_trigger_msg['ueid']
        
        from config.constants import TOPIC_VISION_EVENT
        self.start_time=time.time()
        self.client.publish(TOPIC_VISION_EVENT, json.dumps(vision_trigger_msg))
        self.sent = True
        
        return py_trees.common.Status.RUNNING

    def _process_vision_result(self):
        """Process vision detection result"""
        vision_pick_loc = self.bb.vision_response_msg.pl["location"]
        
        # Create intermediate point at current z-height
        vision_pick_intermediate = type(vision_pick_loc)()
        vision_pick_intermediate['x'] = vision_pick_loc['x']
        vision_pick_intermediate['y'] = vision_pick_loc['y']
        vision_pick_intermediate['z'] = self.bb.current_location['z']
        vision_pick_intermediate['c'] = vision_pick_loc['c']

        vision_pick_loc['z'] = Config.PICKUP_LOC['z']
        print(vision_pick_loc)
        
        setattr(self.bb, "/location/vision_pick_intermediate", vision_pick_intermediate)
        setattr(self.bb, "/location/action", vision_pick_loc)
        post_action_location={}
        post_action_location['x']=vision_pick_loc['x']
        post_action_location['y']=vision_pick_loc['y']
        post_action_location['z']=vision_pick_loc['z']+300
        setattr(self.bb,"/location/postaction",post_action_location)
        self.sent = False