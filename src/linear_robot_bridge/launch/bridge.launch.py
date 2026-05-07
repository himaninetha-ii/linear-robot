from launch import LaunchDescription

from launch_ros.actions import Node

import os

from ament_index_python.packages import (
    get_package_share_directory
)


def generate_launch_description():

    config = os.path.join(
        get_package_share_directory(
            'linear_robot_bridge'
        ),
        'config',
        'mqtt_topics.yaml'
    )

    return LaunchDescription([

        Node(
            package='linear_robot_bridge',
            executable='mqtt_to_ros',
            output='screen',
            parameters=[config]
        )

    ])