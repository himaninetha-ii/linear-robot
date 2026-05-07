"""
Data models for events and responses
"""
from dataclasses import dataclass
from typing import Optional, Any, Dict


@dataclass
class Event:
    """Event message structure"""
    eid: int
    ts: str
    ueid: str
    eg: Optional[str] = None
    ec: Optional[int] = None
    pl: Optional[Dict[str, Any]] = None


@dataclass
class Response:
    """Response message structure"""
    eid: int
    ts: str
    ueid: str
    rc: int
    eg: Optional[str] = None
    pl: Optional[Dict[str, Any]] = None