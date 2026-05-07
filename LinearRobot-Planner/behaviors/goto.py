"""
Navigation behavior nodes
"""
import py_trees
import json
import uuid
from datetime import datetime

from config.constants import IST, Config
from models.enums import EventGroupID, EventID
from utils.geometry import line_circle_intersection


class GoTo(py_trees.behaviour.Behaviour):
    """Navigate robot to a specified location"""
    
    def __init__(self, location_name: str, location_key: str, blackboard, bt_complete_cv=None):
        super().__init__(name=f'GoTo{location_name}')
        self.bb = blackboard
        self.location_name = location_name
        self.location_key = location_key
        self.client = self.bb.client
        self.sent = False
        if self.location_name == "PostAction":
            self.bt_complete_cv=bt_complete_cv

        if self.location_name in ['Intermediate','PreAction','VisionPickIntermediate']:
            self.feedrate=Config.MOVE_FEEDRATE

        elif self.location_name in ['Pick','Place','AccuratePlaceOffset','AccuratePlaceDown',"AccuratePlaceOffsetCorrection",'PostAction']:
            self.feedrate=Config.VERTICAL_FEEDRATE

    def update(self) -> py_trees.common.Status:
        if not self.sent:
            return self._send_move_command()
        
        if self.bb.rc_response is None:
            return py_trees.common.Status.RUNNING
        
        if self.bb.rc_response == 1:
            if self.location_name == "PostAction":
                self.bb.current_task_ueid = None
                with self.bt_complete_cv:
                    self.bt_complete_cv.notify_all()
            self.bb.current_location=self.location
            # print(self.location)
            return py_trees.common.Status.SUCCESS
        
        if self.bb.rc_response == 2:
            return py_trees.common.Status.FAILURE

    def _send_move_command(self) -> py_trees.common.Status:
        """Send movement command to robot"""
        self.location = getattr(self.bb, self.location_key)
        self.bb.rc_response = None
        # print(self.location)
        if 'c' not in self.location.keys():
            self.location['c']=0

        
        move_msg = {
            "eg": EventGroupID.LINEAR_ROBOT.value,
            "eid": EventID.MOVE.value,
            "ts": datetime.now(IST).isoformat(),
            "ueid": str(uuid.uuid4()),
            "ec": None,
            "pl": {
                "location": self.location,
                "feedrate": self.feedrate
            }
        }
        
        self.bb.current_action_ueid = move_msg["ueid"]
        print(f"Moving to {self.location_name}: {move_msg}")
        
        # if self.location_name == "Pick":
        #     input("Press Enter to continue")

        from config.constants import TOPIC_PLANNER_EVENT
        self.client.publish(TOPIC_PLANNER_EVENT, json.dumps(move_msg))
        self.sent = True
        
        return py_trees.common.Status.RUNNING


class IntermediatePoint(py_trees.behaviour.Behaviour):
    """Calculate intermediate waypoint to avoid collisions"""
    
    def __init__(self, point_name: str, blackboard):
        super().__init__(name=f'IntermediatePoint{point_name}')
        self.bb = blackboard
        self.point_name = point_name

    def update(self) -> py_trees.common.Status:
        current_loc = getattr(self.bb, "current_location", {})
        target_loc = getattr(self.bb, "/location/preaction", {})
        action_loc = getattr(self.bb, "action_location", "")
        
        # Determine which circle to use
        circle_center, circle_radius = self._get_circle_params(
            action_loc, current_loc, target_loc
        )
        
        # Calculate intersection point
        try:
            intersection = line_circle_intersection(
                (circle_center['x'], circle_center['y'], circle_center['z']),
                circle_radius,
                (current_loc['x'], current_loc['y']),
                (target_loc['x'], target_loc['y'])
            )
            
            # Create intermediate location
            intermediate_loc = type(current_loc)()
            intermediate_loc['x'] = intersection[0]
            intermediate_loc['y'] = intersection[1]
            intermediate_loc['z'] = max(current_loc['z'], target_loc['z']) + 50
            
            setattr(self.bb, "/location/intermediate", intermediate_loc)
            return py_trees.common.Status.SUCCESS
            
        except ValueError as e:
            print(f"Error calculating intermediate point: {e}")
            return py_trees.common.Status.FAILURE

    def _get_circle_params(self, action_loc, current_loc, target_loc):
        """Determine circle center and radius based on action type"""
        if action_loc == "pallet":
            if current_loc["z"] > target_loc["z"]:
                center = getattr(self.bb, "pick_circle_center", {})
                radius = getattr(self.bb, "pick_circle_radius")+100
            else:
                center = getattr(self.bb, "place_circle_center", {})
                radius = getattr(self.bb, "place_circle_radius")
        else:  # box
            if current_loc["z"] > target_loc["z"]:
                center = getattr(self.bb, "place_circle_center", {})
                radius = getattr(self.bb, "place_circle_radius")
            else:
                center = getattr(self.bb, "pick_circle_center", {})
                radius = getattr(self.bb, "pick_circle_radius")
        
        return center, radius