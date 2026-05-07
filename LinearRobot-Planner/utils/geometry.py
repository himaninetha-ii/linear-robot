"""
Geometric utility functions
"""
import math
from typing import Tuple, List
from config.constants import AVOIDANCE_CONSTANT


def calculate_circle_radius(length: float, width: float, tolerance: float) -> float:
    """Calculate radius of bounding circle with tolerance"""
    return math.sqrt(length**2 + width**2) / 2 + tolerance


def line_circle_intersection(
    center: Tuple[float, float, float],
    radius: float,
    start_pose: Tuple[float, float],
    end_pose: Tuple[float, float]
) -> Tuple[float, float]:
    """
    Find intersection point between line segment and circle
    
    Args:
        center: Circle center (x, y, z)
        radius: Circle radius
        start_pose: Start point (x, y)
        end_pose: End point (x, y)
    
    Returns:
        Intersection point (x, y)
    """
    h, k, z = center
    x1, y1 = start_pose[0:2]
    x2, y2 = end_pose[0:2]
    
    dx, dy = x2 - x1, y2 - y1
    
    # Quadratic coefficients
    a = dx**2 + dy**2
    b = 2 * (dx * (x1 - h) + dy * (y1 - k))
    c = (x1 - h)**2 + (y1 - k)**2 - radius**2
    
    discriminant = b**2 - 4 * a * c
    
    if discriminant < 0:
        raise ValueError("No intersection found between line and circle")
    
    intersections = []
    sqrt_disc = math.sqrt(discriminant)
    
    for sign in (-1, 1):
        t = (-b + sign * sqrt_disc) / (2 * a)
        if 0 <= t <= 1:  # within segment
            x = x1 + t * dx
            y = y1 + t * dy
            intersections.append((x, y))
    
    if not intersections:
        raise ValueError("No intersection within line segment")
    
    return intersections[0]

def line_square_intersection(initial_corner,pallet_length,pallet_width,start_pose,end_pose):

    xi, yi = end_pose['x'],end_pose['y']
    xo, yo = start_pose['x'],start_pose['y']
    dx = xo - xi
    dy = yo - yi

    candidates = []

    # Vertical sides
    for x_edge in (initial_corner['x']-AVOIDANCE_CONSTANT, initial_corner['x'] + pallet_width+AVOIDANCE_CONSTANT):
        if dx != 0:
            t = (x_edge - xi) / dx
            if t > 0 and t<1:
                y = yi + t * dy
                if initial_corner['y']-AVOIDANCE_CONSTANT <= y <= initial_corner['y'] + pallet_length+AVOIDANCE_CONSTANT:
                    candidates.append((t, (x_edge, y)))

    # Horizontal sides
    for y_edge in (initial_corner['y']-AVOIDANCE_CONSTANT, initial_corner['y'] + pallet_length+AVOIDANCE_CONSTANT):
        if dy != 0:
            t = (y_edge - yi) / dy
            if t > 0 and t<1:
                x = xi + t * dx
                if initial_corner['x']-AVOIDANCE_CONSTANT <= x <= initial_corner['x'] + pallet_width+AVOIDANCE_CONSTANT:
                    candidates.append((t, (x, y_edge)))

    if not candidates:
        return None

    # Closest intersection
    return min(candidates, key=lambda c: c[0])[1]