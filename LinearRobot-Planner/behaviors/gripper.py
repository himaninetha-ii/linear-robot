"""
Gripper control behavior nodes
"""
import py_trees
import json
import uuid
from datetime import datetime

from config.constants import IST
from models.enums import EventGroupID, EventID


class EOATAction(py_trees.behaviour.Behaviour):
    """Execute end-of-arm tooling (gripper) action"""
    
    def __init__(self, action_name: str, action_key: str, blackboard):
        super().__init__(name=f'EOATAction{action_name}')
        self.bb = blackboard
        self.action_key = action_key
        self.client = self.bb.client
        self.sent = False

    def update(self) -> py_trees.common.Status:
        if not self.sent:
            return self._send_gripper_command()
        
        if self.bb.rc_response is None:
            return py_trees.common.Status.RUNNING
        
        if self.bb.rc_response == 1:
            return py_trees.common.Status.SUCCESS
        
        if self.bb.rc_response == 2:
            return py_trees.common.Status.FAILURE

    def _send_gripper_command(self) -> py_trees.common.Status:
        """Send gripper control command"""
        gripper_action = getattr(self.bb, self.action_key)
        self.bb.rc_response = None
        
        gripper_msg = {
            "eg": EventGroupID.GRIPPER,
            "eid": (EventID.GRIPPER_ON if gripper_action == "on" 
                   else EventID.GRIPPER_OFF),
            "ts": datetime.now(IST).isoformat(),
            "ueid": str(uuid.uuid4()),
            "ec": None,
            "pl": {}
        }
        print(gripper_msg)
        
        self.bb.current_action_ueid = gripper_msg["ueid"]
        
        from config.constants import TOPIC_PLANNER_EVENT
        self.client.publish(TOPIC_PLANNER_EVENT, json.dumps(gripper_msg), qos=1, retain=False)
        self.sent = True
        
        return py_trees.common.Status.RUNNING