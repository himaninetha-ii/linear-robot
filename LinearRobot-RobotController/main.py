#!/usr/bin/env python3
"""Entry point for the Linear Robot Controller."""

from controller.robot_controller import RobotController


def main():
    """Initialize and run the robot controller."""
    print("Starting Linear Robot Controller...")
    controller = RobotController()
    
    try:
        controller.run()
    except KeyboardInterrupt:
        print("\nStopping controller...")


if __name__ == "__main__":
    main()