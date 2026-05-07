#!/usr/bin/env python3
"""
Main entry point for LinearRobot Task Executor
"""
import argparse
import time

from src.core import TaskExecutor


def main():
    """Main execution function"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='LinearRobot Task Executor')
    parser.add_argument("--program", type=str, required=True, help='Program to execute')
    args = parser.parse_args()
    
    # Initialize task executor
    executor = TaskExecutor(program_name=args.program)
    
    # Verify if there's an incomplete task
    executor.verify_task_completion()
    
    # Wait for user response or proceed with execution
    while True:
        time.sleep(1)
        if executor.received:
            executor.start()
            break


if __name__ == "__main__":
    main()