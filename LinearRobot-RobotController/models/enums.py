"""Enumerations for event and group IDs."""
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
    RESTART = 10020


class EventGroupID(IntEnum):
    """Event group identifiers."""
    LINEAR_ROBOT = 10000
    GRIPPER = 11000
    SERVO = 12000
    SYSTEM = 13000
    VISION = 14000