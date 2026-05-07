"""Response data model"""
from dataclasses import dataclass
from typing import Optional, Any, Dict


@dataclass
class Response:
    """Response message structure"""
    eid: int
    ts: str
    ueid: str
    rc: int
    eg: Optional[str] = None
    pl: Optional[Dict[str, Any]] = None
