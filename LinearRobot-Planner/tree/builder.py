"""
Behavior tree construction
"""
import py_trees
import math

from behaviors import GoTo, IntermediatePoint
from behaviors.gripper import EOATAction
from behaviors.vision import VisionPick
from behaviors.conditions import Condition
from models.enums import TaskID
from config.constants import Config
from utils.geometry import calculate_circle_radius

from models.enums import TaskID


class BehaviorTreeBuilder:
    """Build the robot control behavior tree"""
    
    def __init__(self, blackboard,bt_complete_cv):
        self.bb = blackboard
        self.bt_complete_cv=bt_complete_cv

    def build(self) -> py_trees.trees.BehaviourTree:
        """Construct the complete behavior tree"""
        root = py_trees.composites.Selector("Root", memory=False)
        
        action_sequence = self._build_action_sequence()
        root.add_child(action_sequence)
        
        fallback = py_trees.behaviours.Failure(name="Fallback")
        root.add_child(fallback)
        
        return py_trees.trees.BehaviourTree(root)

    def _build_action_sequence(self):
        """Build main action sequence"""
        action_sequence = py_trees.composites.Sequence("Action Sequence", memory=True)
        
        preaction = self._build_preaction()
        action = self._build_action()
        postaction = self._build_postaction()
        
        action_sequence.add_children([preaction, action, postaction])
        return action_sequence

    def _build_preaction(self):
        """Build pre-action sequence (approach)"""
        preaction = py_trees.composites.Sequence("PreAction Sequence", memory=True)
        
        # Intermediate point to avoid collisions
        intermediate_seq = py_trees.composites.Sequence("Intermediate Point Sequence", memory=True)
        intermediate_point = IntermediatePoint("PreActionIntermediatePoint", self.bb)
        go_to_intermediate = GoTo("Intermediate", "/location/intermediate", self.bb)
        intermediate_seq.add_children([intermediate_point, go_to_intermediate])
        
        # Final pre-action position
        final_preaction = GoTo("PreAction", "/location/preaction", self.bb)
        
        preaction.add_children([intermediate_seq, final_preaction])
        return preaction

    def _build_action(self):
        """Build main action sequence (pick/place)"""
        action = py_trees.composites.Sequence("Action Sequence", memory=True)
        
        pick_place = py_trees.composites.Sequence("Pick or Place Sequence", memory=True)
        
        # Pick selector
        pick_sel = self._build_pick_selector()
        
        # Place selector
        place_sel = self._build_place_selector()
        
        pick_place.add_children([pick_sel, place_sel])
        
        # Gripper action
        gripper_action = EOATAction("GripperAction", "gripper_action", self.bb)
        
        action.add_children([pick_place, gripper_action])
        return action

    def _build_pick_selector(self):
        """Build pick operation selector"""
        pick_sel = py_trees.composites.Selector("Pick Selector", memory=True)
        
        # Check if this is a pick operation
        pick_dec = py_trees.decorators.Inverter(
            name="Pick Decorator",
            child=Condition(
                "Pick Condition",
                condition=lambda: (getattr(self.bb, "event", None) and 
                                  self.bb.event.eid == TaskID.PICK)
            )
        )
        
        # Pick type sequence
        pick_type_seq = py_trees.composites.Sequence("Pick Type Sequence", memory=True)
        
        # Vision pick selector
        pick_type_sel = py_trees.composites.Selector("Pick Type Selector", memory=True)
        pick_type_dec = py_trees.decorators.Inverter(
            name="Pick Type Decorator",
            child=Condition(
                "Pick Type Condition",
                condition=lambda: (getattr(self.bb, "current_action_type", None) and 
                                  self.bb.current_action_type == "vision_pick")
            )
        )
        
        # Vision pick sequence
        vision_pick_seq = py_trees.composites.Sequence("Vision Pick Sequence", memory=True)
        vision_pick = VisionPick("Vision Pick", self.bb)
        vision_pick_retry=py_trees.decorators.Retry(child=vision_pick,name='retry_vision_pick',num_failures=1000)
        go_to_vision_intermediate = GoTo("VisionPickIntermediate", 
                                         "/location/vision_pick_intermediate", self.bb)
        vision_pick_seq.add_children([vision_pick_retry, go_to_vision_intermediate])
        
        pick_type_sel.add_children([pick_type_dec, vision_pick_seq])
        
        # Final pick location
        go_to_pick = GoTo("Pick", "/location/action", self.bb)
        pick_type_seq.add_children([pick_type_sel, go_to_pick])
        
        pick_sel.add_children([pick_dec, pick_type_seq])
        return pick_sel

    def _build_place_selector(self):
        """Build place operation selector"""
        place_sel = py_trees.composites.Selector("Place Selector", memory=True)
        
        # Check if this is a place operation
        place_dec = py_trees.decorators.Inverter(
            name="Place Decorator",
            child=Condition(
                "Place Condition",
                condition=lambda: (getattr(self.bb, "event", None) and 
                                  self.bb.event.eid == TaskID.PLACE)
            )
        )
        
        # Place type sequence
        place_type_seq = py_trees.composites.Sequence("Place Type Sequence", memory=True)
        
        # Accurate place selector
        place_type_sel = py_trees.composites.Selector("Place Type Selector", memory=True)
        place_type_dec = py_trees.decorators.Inverter(
            name="Place Type Decorator",
            child=Condition(
                "Place Type Condition",
                condition=lambda: (getattr(self.bb, "current_action_type", None) and 
                                  self.bb.current_action_type == "accurate_place")
            )
        )
        
        # Accurate place sequence
        accurate_place = py_trees.composites.Sequence("Accurate Place Sequence", memory=True)
        offset_place = GoTo("AccuratePlaceOffset", "/location/accurate_place/offset", self.bb)
        down_place = GoTo("AccuratePlaceDown", "/location/accurate_place/down", self.bb)
        offset_correction = GoTo("AccuratePlaceOffsetCorrection", 
                                "/location/accurate_place/offset_correction", self.bb)
        accurate_place.add_children([down_place, offset_correction])
        
        place_type_sel.add_children([place_type_dec, accurate_place])
        
        # Final place location
        go_to_place = GoTo("Place", "/location/action", self.bb)
        place_type_seq.add_children([place_type_sel, go_to_place])
        
        place_sel.add_children([place_dec, place_type_seq])
        return place_sel

    def _build_postaction(self):
        """Build post-action sequence (retreat)"""
        postaction = py_trees.composites.Sequence("PostAction Sequence", memory=True)
        go_to_postaction = GoTo("PostAction", "/location/postaction", self.bb,self.bt_complete_cv)
        postaction.add_child(go_to_postaction)
        return postaction


def calculate_locations(event, bb,action_location):
    """Calculate all required locations for a task"""
    locations = {}
    
    locations["action_location"] = action_location
    locations["/location/action"] = event.pl.get("location", {})
    
    if event.eid==TaskID.PICK:
        z_offset=Config.Z_OFFSET_PICK
    elif event.eid==TaskID.PLACE:
        z_offset=Config.Z_OFFSET_PLACE
    # Pre-action location (above target)
    locations["/location/preaction"] = locations["/location/action"].copy()
    locations["/location/preaction"]["z"] = locations["/location/action"]["z"] + z_offset
    
    # Post-action location (above target)
    locations["/location/postaction"] = locations["/location/action"].copy()
    locations["/location/postaction"]["z"] = locations["/location/action"]["z"] + z_offset
    
    # Accurate place locations
    locations["/location/accurate_place/offset"] = locations["/location/preaction"].copy()
    locations["/location/accurate_place/offset"]["x"] += Config.ACCURATE_PLACE_OFFSET
    locations["/location/accurate_place/offset"]["y"] += Config.ACCURATE_PLACE_OFFSET
    
    locations["/location/accurate_place/down"] = locations["/location/accurate_place/offset"].copy()
    locations["/location/accurate_place/down"]["z"] = (
        locations["/location/action"]["z"] + Config.ACCURATE_PLACE_OFFSET
    )
    if bb.current_action_type == "accurate_place":
        locations["/location/preaction"] = locations["/location/accurate_place/offset"].copy()
    
    locations["/location/accurate_place/offset_correction"] = locations["/location/action"].copy()
    locations["/location/accurate_place/offset_correction"]["z"] += Config.ACCURATE_PLACE_OFFSET
    
    return locations


def calculate_state_values(event, current_action):
    """Calculate state values for a task"""
    state = {}
    
    state["current_task_ueid"] = event.ueid
    state["current_action"] = current_action
    state["current_action_type"] = event.pl.get("action_type", "")
    
    # Circle parameters for collision avoidance
    state["pick_circle_center"] = Config.PICKUP_LOC
    state["pick_circle_radius"] = calculate_circle_radius(
        Config.BOX_LENGTH, Config.BOX_WIDTH, Config.INTERMEDIATE_POINT_TOLERANCE
    )
    
    state["place_circle_center"] = {
        'x': Config.INITIAL_CORNER['x'] + Config.PALLET_LENGTH / 2,
        'y': Config.INITIAL_CORNER['y'] + Config.PALLET_WIDTH / 2,
        'z': 0
    }
    state["place_circle_radius"] = calculate_circle_radius(
        Config.PALLET_LENGTH, Config.PALLET_WIDTH, Config.INTERMEDIATE_POINT_TOLERANCE
    )
    
    # Gripper action
    state["gripper_action"] = "on" if current_action == "pick" else "off"
    
    return state