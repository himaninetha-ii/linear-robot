from enum import IntEnum

class EventID(IntEnum):
    """Event identifiers for robot commands."""
    MOVE = 10001
    GRIPPER_ON = 10002
    GRIPPER_OFF = 10003
    SERVO_ON = 10004
    SERVO_OFF = 10005
    PAUSE = 10006
    RESUME = 10007
    RESET = 10008
    PING = 10009
    TELEMETRY = 10010
    RESTART = 10020


class EventGroupID(IntEnum):
    """Event group identifiers."""
    LINEAR_ROBOT_EVENT = 10000
    GRIPPER_EVENT = 11000
    SERVO_EVENT = 12000
    SYSTEM_EVENT = 13000
    VISION_EVENT = 14000


class ResponseStatus(IntEnum):
    """Response status codes."""
    SUCCESS = 1
    FAILURE = 2