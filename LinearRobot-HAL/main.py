"""Main entry point for the Linear Robot HAL system."""

from hal.robot_hal import LinearRobotHAL

def main():
    """Initialize and start the Linear Robot HAL."""
    try:
        hal = LinearRobotHAL()
        hal.start()
    except KeyboardInterrupt:
        print("\nShutting down Linear Robot HAL...")
    except Exception as e:
        print(f"Fatal error: {e}")
        raise


if __name__ == "__main__":
    main()