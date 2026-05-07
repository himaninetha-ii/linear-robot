"""Data models for events, responses, and telemetry."""
from dataclasses import dataclass
from typing import Optional, Any


@dataclass
class Event:
    """Represents an event from the planner."""
    eid: int
    ts: str
    ueid: str
    eg: Optional[str] = None
    ec: Optional[int] = None
    pl: Optional[dict[str, Any]] = None


@dataclass
class Response:
    """Represents a response from the HAL."""
    eid: int
    ts: str
    ueid: str
    rc: int
    eg: Optional[str] = None
    pl: Optional[dict[str, Any]] = None


@dataclass
class Telemetry:
    """Represents telemetry data from the HAL."""
    eid: int
    ts: str
    ueid: str
    eg: Optional[str] = None
    pl: Optional[dict[str, Any]] = None