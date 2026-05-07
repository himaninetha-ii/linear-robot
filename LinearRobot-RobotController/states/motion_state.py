"""Motion state machine for robot movement control."""
from transitions import Machine
from models.enums import EventGroupID, EventID


class MotionState:
    """Manages the motion state of the robot."""
    
    STATES = ['move', 'paused', 'enabled', 'disabled']

    def __init__(self, parent):
        self.parent = parent
        self.last_state = None
        
        # Initialize state machine
        self.machine = Machine(
            model=self,
            states=self.STATES,
            initial='disabled'
        )
        
        # Define transitions
        self._setup_transitions()

    def _setup_transitions(self):
        """Configure all state transitions."""
        transitions = [
            {'trigger': 'enable', 'source': 'disabled', 'dest': 'enabled', 'before': 'start_servo'},
            {'trigger': 'disable', 'source': 'enabled', 'dest': 'disabled', 'before': 'stop_servo'},
            {'trigger': 'move', 'source': 'enabled', 'dest': 'move', 'before': 'move_to_target'},
            {'trigger': 'pause', 'source': ['disabled','enabled', 'move'], 'dest': 'paused', 'before': 'pause_movement'},
            {'trigger': 'resume', 'source': ['disabled','enabled', 'paused','move'], 'dest': 'enabled', 'before': 'resume_movement','after': 'after_resume'},
            {'trigger': 'home', 'source': ['enabled', 'paused', 'move','disabled'], 'dest': 'enabled', 'before': 'reset_position'},
        ]
        
        for trans in transitions:
            self.machine.add_transition(**trans)

    def move_to_target(self):
        """Move robot to target position."""
        print("Moving to target position")
        payload = {
            "target_position": self.parent.target,
            "feedrate": self.parent.feedrate
        }
        msg = self.parent.create_message(
            EventGroupID.LINEAR_ROBOT,
            EventID.MOVE,
            payload=payload
        )
        self.parent.publish_event(msg)

    def pause_movement(self):
        """Pause current movement."""
        print("Pausing movement")
        self.last_state = self.state
        msg = self.parent.create_message(EventGroupID.LINEAR_ROBOT, EventID.PAUSE)
        self.parent.publish_event(msg)

    def resume_movement(self):
        """Resume from paused state."""
        print("Resuming movement")
        msg = self.parent.create_message(EventGroupID.LINEAR_ROBOT, EventID.RESUME)
        self.parent.publish_event(msg)

    def after_resume(self):
        self.state=self.last_state
        
    def reset_position(self):
        """Reset robot to home position."""
        print("Resetting position")
        msg = self.parent.create_message(EventGroupID.LINEAR_ROBOT, EventID.RESET)
        self.parent.publish_event(msg)

    def start_servo(self):
        """Enable servo motors."""
        print("Starting servo")
        msg = self.parent.create_message(EventGroupID.LINEAR_ROBOT, EventID.SERVO_ON)
        self.parent.publish_event(msg)
    
    def stop_servo(self):
        """Disable servo motors."""
        print("Stopping servo")
        msg = self.parent.create_message(EventGroupID.LINEAR_ROBOT, EventID.SERVO_OFF)
        self.parent.publish_event(msg)