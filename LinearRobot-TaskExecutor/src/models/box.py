"""Box data model"""
from dataclasses import dataclass


@dataclass
class Box:
    """Represents a box with dimensions and placement information"""
    length: int  # length
    breadth: int  # breadth
    height: int  # height
    position: dict  # position
    rotation: int  # type/orientation
    placement_order: int  # order
