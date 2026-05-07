"""Gripper state machine for gripper control."""
from transitions import Machine
from models.enums import EventGroupID, EventID


class GripperState:
    """Manages the gripper state."""
    
    STATES = ['on', 'off']

    def __init__(self, parent):
        self.parent = parent
        
        # Initialize state machine
        self.machine = Machine(
            model=self,
            states=self.STATES,
            initial='off',
            ignore_invalid_triggers=True
        )
        
        # Define transitions
        self._setup_transitions()

    def _setup_transitions(self):
        """Configure gripper transitions."""
        self.machine.add_transition(
            trigger='turn_off',
            source='on',
            dest='off',
            before='release_object'
        )
        self.machine.add_transition(
            trigger='turn_on',
            source='off',
            dest='on',
            before='grip_object'
        )

    def grip_object(self):
        """Activate gripper to grip object."""
        print("Gripping object")
        msg = self.parent.create_message(EventGroupID.GRIPPER, EventID.GRIPPER_ON)
        self.parent.publish_event(msg)

    def release_object(self):
        """Release gripper."""
        print("Releasing object")
        msg = self.parent.create_message(EventGroupID.GRIPPER, EventID.GRIPPER_OFF)
        self.parent.publish_event(msg)