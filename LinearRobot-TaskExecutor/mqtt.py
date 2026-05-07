#!/usr/bin/env python3
"""
MQTT Client that listens for start signals and launches main.py
"""
from src.core import MQTTTrigger


def main():
    """Main execution function"""
    # Initialize and run MQTT trigger
    trigger = MQTTTrigger()
    trigger.run()


if __name__ == "__main__":
    main()
