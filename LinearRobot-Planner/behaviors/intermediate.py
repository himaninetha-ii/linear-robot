import py_trees
import json
import uuid
from datetime import datetime

from config.constants import IST,Config
from models.enums import EventGroupID, EventID
from utils.geometry import line_circle_intersection, line_square_intersection

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
        # print(circle_center,circle_radius)
        
        # Calculate intersection point
        try:
            if self.bb.current_action=='pick':
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
                intermediate_loc['z'] = max(current_loc['z'], target_loc['z'])
                
                setattr(self.bb, "/location/intermediate", intermediate_loc)
                return py_trees.common.Status.SUCCESS

            elif self.bb.current_action=='place':
                initial_corner=Config.INITIAL_CORNER
                pallet_length=Config.PALLET_LENGTH
                pallet_width=Config.PALLET_WIDTH
                intersection=line_square_intersection(
                    initial_corner, pallet_length, pallet_width, current_loc, target_loc
                )
                intermediate_loc = type(current_loc)()
                intermediate_loc['x'] = intersection[0]
                intermediate_loc['y'] = intersection[1]
                intermediate_loc['z'] = max(current_loc['z'], target_loc['z'])
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