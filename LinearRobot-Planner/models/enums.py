"""
Enum definitions for events, tasks, and groups
"""
from enum import IntEnum


class TaskID(IntEnum):
    """Task identifiers"""
    PICK = 10022
    PLACE = 10023


class EventID(IntEnum):
    """Event identifiers"""
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
    VISION = 10030


class EventGroupID(IntEnum):
    """Event group identifiers"""
    LINEAR_ROBOT = 10000
    GRIPPER = 11000
    SERVO = 12000
    SYSTEM = 13000
    VISION = 14000