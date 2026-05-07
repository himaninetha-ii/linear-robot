from setuptools import setup

package_name = 'linear_robot_bridge'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        (
            'share/ament_index/resource_index/packages',
            ['resource/' + package_name]
        ),
        (
            'share/' + package_name,
            ['package.xml']
        ),
        (
            'share/' + package_name + '/launch',
            ['launch/bridge.launch.py']
        ),
        (
            'share/' + package_name + '/config',
            ['config/mqtt_topics.yaml']
        ),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='himani',
    maintainer_email='himani@example.com',
    description='MQTT to ROS2 bridge for gantry robot',
    license='Apache License 2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'mqtt_to_ros = linear_robot_bridge.mqtt_to_ros:main',
        ],
    },
)