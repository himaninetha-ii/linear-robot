"""Event data models"""
from dataclasses import dataclass
from typing import Optional, Any
from enum import IntEnum


@dataclass
class Event:
    """Represents an event from the planner."""
    eid: int
    ts: str
    ueid: str
    eg: Optional[str] = None
    ec: Optional[int] = None
    pl: Optional[dict[str, Any]] = None


class EventID(IntEnum):
    """Event identifiers for robot commands."""
    START = 10051
    RESET = 10008
