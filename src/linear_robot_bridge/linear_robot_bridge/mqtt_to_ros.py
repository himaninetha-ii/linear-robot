import json
import math
from datetime import datetime

import paho.mqtt.client as mqtt
import rclpy
from builtin_interfaces.msg import Duration
from rclpy.node import Node
from sensor_msgs.msg import JointState
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint


class MQTTBridge(Node):

    def __init__(self):
        super().__init__('mqtt_bridge')

        self.declare_parameter('mqtt_broker', 'localhost')
        self.declare_parameter('mqtt_port', 1883)
        self.declare_parameter('mqtt_topic', 'LinearRobotTask/event')
        self.declare_parameter('mqtt_response_topic', 'LinearRobot/response')
        self.declare_parameter('controller_topic', '/gantry_controller/joint_trajectory')
        self.declare_parameter('gripper_controller_topic', '/gripper_controller/joint_trajectory')
        self.declare_parameter('default_feedrate', 6000.0)
        self.declare_parameter('joint_names', ['y_joint', 'x_joint', 'z_joint', 'wrist_joint'])

        mqtt_broker = self.get_parameter('mqtt_broker').value
        mqtt_port = self.get_parameter('mqtt_port').value
        self.mqtt_topic = self.get_parameter('mqtt_topic').value
        self.mqtt_response_topic = self.get_parameter('mqtt_response_topic').value
        controller_topic = self.get_parameter('controller_topic').value
        gripper_controller_topic = self.get_parameter('gripper_controller_topic').value
        self.default_feedrate = float(self.get_parameter('default_feedrate').value)
        self.joint_names = self.get_parameter('joint_names').value

        self.trajectory_pub = self.create_publisher(JointTrajectory, controller_topic, 10)
        self.gripper_pub = self.create_publisher(JointTrajectory, gripper_controller_topic, 10)
        self.joint_state_sub = self.create_subscription(JointState, '/joint_states', self.joint_state_callback, 10)

        self.current_joint_positions = {
            'y_joint': 0.0,
            'x_joint': 0.0,
            'z_joint': 0.0,
            'wrist_joint': 0.0,
            'left_finger_joint': 0.0,
        }
        self.active_goal = None

        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        self.get_logger().info(f'Connecting MQTT: {mqtt_broker}:{mqtt_port}')
        self.client.connect(mqtt_broker, mqtt_port, 60)
        self.client.loop_start()

        self.get_logger().info(f'Publishing gantry trajectories to: {controller_topic}')
        self.get_logger().info(f'Publishing gripper trajectories to: {gripper_controller_topic}')

    def on_connect(self, client, userdata, flags, rc):
        self.get_logger().info('Connected to MQTT broker')
        client.subscribe(self.mqtt_topic)
        self.get_logger().info(f'Subscribed to topic: {self.mqtt_topic}')

    def on_message(self, client, userdata, msg):
        message = msg.payload.decode()
        self.get_logger().info(f'Received MQTT message: {message}')

        try:
            event = json.loads(message)
            payload = event.get('pl', {})
            event_name = str(payload.get('event', payload.get('command', 'MOVE'))).upper()

            if event_name in {'GRIPPER_CLOSE', 'CLOSE_GRIPPER', 'GRIPPER_ON'}:
                self.handle_gripper_event(event, close_gripper=True)
                return
            if event_name in {'GRIPPER_OPEN', 'OPEN_GRIPPER', 'GRIPPER_OFF'}:
                self.handle_gripper_event(event, close_gripper=False)
                return

            self.handle_move_event(event)
        except Exception as exc:
            self.get_logger().error(f'Error processing MQTT message: {exc}')

    def handle_move_event(self, event):
        payload = event.get('pl', {})
        target = payload.get('target_position', payload.get('location', {}))

        x_mm = float(target.get('x', 0.0))
        y_mm = float(target.get('y', 0.0))
        z_mm = float(target.get('z', 0.0))
        c_deg = float(target.get('c', 0.0))

        feedrate = float(payload.get('feedrate', self.default_feedrate))

        # RobotController mapping: x->y_joint, y->x_joint, z->z_joint
        target_positions = {
            'y_joint': x_mm / 1000.0,
            'x_joint': y_mm / 1000.0,
            'z_joint': z_mm / 1000.0,
            'wrist_joint': math.radians(c_deg),
        }

        current_y = self.current_joint_positions.get('y_joint', 0.0)
        current_x = self.current_joint_positions.get('x_joint', 0.0)
        current_z = self.current_joint_positions.get('z_joint', 0.0)

        dx = target_positions['y_joint'] - current_y
        dy = target_positions['x_joint'] - current_x
        dz = target_positions['z_joint'] - current_z
        distance = math.sqrt(dx * dx + dy * dy + dz * dz)

        velocity_mps = (feedrate / 1000.0) / 60.0
        if velocity_mps < 0.001:
            velocity_mps = 0.001

        move_time = distance / velocity_mps if distance > 0.0 else 0.1
        if move_time < 0.1:
            move_time = 0.1

        traj = JointTrajectory()
        traj.joint_names = ['y_joint', 'x_joint', 'z_joint', 'wrist_joint']

        point = JointTrajectoryPoint()
        point.positions = [
            target_positions['y_joint'],
            target_positions['x_joint'],
            target_positions['z_joint'],
            target_positions['wrist_joint'],
        ]
        point.velocities = [velocity_mps, velocity_mps, velocity_mps, 0.5]

        sec = int(move_time)
        nanosec = int((move_time - sec) * 1e9)
        point.time_from_start = Duration(sec=sec, nanosec=nanosec)

        traj.points.append(point)

        self.active_goal = {
            'ueid': event.get('ueid', ''),
            'eid': event.get('eid', ''),
            'target': target_positions,
        }

        self.get_logger().info(
            f'Publishing trajectory X={x_mm} Y={y_mm} Z={z_mm} time={move_time:.2f}s'
        )
        self.trajectory_pub.publish(traj)

    def joint_state_callback(self, msg: JointState):
        for i, name in enumerate(msg.name):
            self.current_joint_positions[name] = msg.position[i]

        if self.active_goal is None:
            return

        target = self.active_goal['target']
        tolerance = 0.005

        y_ok = abs(self.current_joint_positions.get('y_joint', 0.0) - target['y_joint']) < tolerance
        x_ok = abs(self.current_joint_positions.get('x_joint', 0.0) - target['x_joint']) < tolerance
        z_ok = abs(self.current_joint_positions.get('z_joint', 0.0) - target['z_joint']) < tolerance

        if y_ok and x_ok and z_ok:
            self.get_logger().info('Trajectory completed')
            response = {
                'eid': self.active_goal['eid'],
                'ueid': self.active_goal['ueid'],
                'ts': datetime.now().isoformat(),
                'rc': 1,
            }
            self.client.publish(self.mqtt_response_topic, json.dumps(response))
            self.active_goal = None

    def handle_gripper_event(self, event, close_gripper):
        traj = JointTrajectory()
        traj.joint_names = ['left_finger_joint']

        point = JointTrajectoryPoint()
        point.positions = [0.0 if close_gripper else 0.04]
        point.time_from_start = Duration(sec=1, nanosec=0)

        traj.points.append(point)
        self.gripper_pub.publish(traj)

        response = {
            'eid': event.get('eid', ''),
            'ueid': event.get('ueid', ''),
            'ts': datetime.now().isoformat(),
            'rc': 1,
        }
        self.client.publish(self.mqtt_response_topic, json.dumps(response))


def main(args=None):
    rclpy.init(args=args)
    node = MQTTBridge()
    node.get_logger().info('MQTT -> ROS2 bridge running')
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
