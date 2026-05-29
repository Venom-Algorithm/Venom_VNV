#!/usr/bin/env python3

import argparse
import math
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import rclpy
import yaml
from geometry_msgs.msg import PoseStamped
from piper_msgs.msg import PosCmd
from rclpy.node import Node
from scipy.spatial.transform import Rotation
from venom_manipulation_interfaces.msg import GraspTarget


def load_pick_params(config_path: Path) -> Dict[str, Any]:
    with config_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    try:
        return data["pick_place_server"]["ros__parameters"]
    except Exception as exc:
        raise RuntimeError(f"Failed to load pick_place_server params from {config_path}") from exc


def xyz_from_list(values: Any, name: str) -> Tuple[float, float, float]:
    if not isinstance(values, list) or len(values) != 3:
        raise RuntimeError(f"{name} must be a 3-element list, got {values!r}")
    return float(values[0]), float(values[1]), float(values[2])


def pose_matrix(position: Tuple[float, float, float], quaternion_xyzw: Tuple[float, float, float, float]):
    matrix = [[0.0] * 4 for _ in range(4)]
    rotation = Rotation.from_quat(quaternion_xyzw).as_matrix()
    for row in range(3):
        for col in range(3):
            matrix[row][col] = float(rotation[row][col])
    matrix[0][3], matrix[1][3], matrix[2][3] = position
    matrix[3][3] = 1.0
    return matrix


def invert_transform(matrix):
    rotation = [[matrix[r][c] for c in range(3)] for r in range(3)]
    translation = [matrix[r][3] for r in range(3)]
    rotation_t = [[rotation[c][r] for c in range(3)] for r in range(3)]
    inverted = [[0.0] * 4 for _ in range(4)]
    for row in range(3):
        for col in range(3):
            inverted[row][col] = rotation_t[row][col]
        inverted[row][3] = -sum(rotation_t[row][k] * translation[k] for k in range(3))
    inverted[3][3] = 1.0
    return inverted


def multiply_transform(a, b):
    result = [[0.0] * 4 for _ in range(4)]
    for row in range(4):
        for col in range(4):
            result[row][col] = sum(a[row][k] * b[k][col] for k in range(4))
    return result


def matrix_to_pose(matrix):
    position = (matrix[0][3], matrix[1][3], matrix[2][3])
    rotation = Rotation.from_matrix([[matrix[r][c] for c in range(3)] for r in range(3)])
    quat = rotation.as_quat()
    rpy = rotation.as_euler("xyz", degrees=False)
    return position, (float(quat[0]), float(quat[1]), float(quat[2]), float(quat[3])), (
        float(rpy[0]), float(rpy[1]), float(rpy[2])
    )


class VisualTargetProbe(Node):
    def __init__(self, timeout_sec: float) -> None:
        super().__init__("visual_target_probe")
        self.timeout_sec = timeout_sec
        self.grasp_target: Optional[GraspTarget] = None
        self.end_pose: Optional[PoseStamped] = None
        self.create_subscription(GraspTarget, "/perception/grasp_target", self._on_target, 10)
        self.create_subscription(PoseStamped, "/end_pose_stamped", self._on_end_pose, 10)
        self.pos_pub = self.create_publisher(PosCmd, "/pos_cmd", 10)

    def _on_target(self, msg: GraspTarget) -> None:
        self.grasp_target = msg

    def _on_end_pose(self, msg: PoseStamped) -> None:
        self.end_pose = msg

    def wait_for_messages(self) -> None:
        deadline = self.get_clock().now().nanoseconds / 1e9 + self.timeout_sec
        while rclpy.ok():
            rclpy.spin_once(self, timeout_sec=0.1)
            now_sec = self.get_clock().now().nanoseconds / 1e9
            if self.grasp_target is not None:
                return
            if now_sec >= deadline:
                raise TimeoutError("Timed out waiting for /perception/grasp_target")

    def publish_pos_cmd(self, position, rpy, gripper_open_m: float) -> None:
        msg = PosCmd()
        msg.x = float(position[0])
        msg.y = float(position[1])
        msg.z = float(position[2])
        msg.roll = float(rpy[0])
        msg.pitch = float(rpy[1])
        msg.yaw = float(rpy[2])
        msg.gripper = float(gripper_open_m)
        msg.mode1 = 0
        msg.mode2 = 0
        self.pos_pub.publish(msg)


def fmt_xyz(values: Tuple[float, float, float]) -> str:
    return f"({values[0]:.4f}, {values[1]:.4f}, {values[2]:.4f})"


def fmt_quat(values: Tuple[float, float, float, float]) -> str:
    return f"({values[0]:.4f}, {values[1]:.4f}, {values[2]:.4f}, {values[3]:.4f})"


def fmt_rpy(values: Tuple[float, float, float]) -> str:
    return (
        f"({values[0]:.4f}, {values[1]:.4f}, {values[2]:.4f}) rad / "
        f"({math.degrees(values[0]):.1f}, {math.degrees(values[1]):.1f}, {math.degrees(values[2]):.1f}) deg"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe the latest visual target and derive grasp/pregrasp poses.")
    parser.add_argument(
        "--config",
        default="manipulation/piper_mtc_tasks/config/real_pick_task.yaml",
        help="Path to the pick task yaml config.",
    )
    parser.add_argument("--timeout", type=float, default=5.0, help="Seconds to wait for ROS topics.")
    parser.add_argument(
        "--publish",
        choices=["none", "grasp", "pregrasp"],
        default="none",
        help="Optionally publish the derived pose to /pos_cmd for direct end-pose validation.",
    )
    parser.add_argument(
        "--gripper-open-m",
        type=float,
        default=0.010,
        help="Gripper opening sent with /pos_cmd when --publish is used.",
    )
    args = parser.parse_args()

    config_path = Path(args.config)
    params = load_pick_params(config_path)
    tcp_offset = xyz_from_list(params.get("tcp_offset_xyz", [0.0, 0.0, 0.0]), "tcp_offset_xyz")
    grasp_target_offset = xyz_from_list(
        params.get("grasp_target_offset_xyz", [0.0, 0.0, 0.0]),
        "grasp_target_offset_xyz",
    )
    pregrasp_offset = xyz_from_list(
        params.get("pregrasp_offset_xyz", [0.0, 0.0, 0.0]),
        "pregrasp_offset_xyz",
    )
    grasp_orientation_rpy = xyz_from_list(
        params.get("grasp_orientation_rpy", [math.pi, 0.0, 0.0]),
        "grasp_orientation_rpy",
    )

    target_rotation = Rotation.from_euler("xyz", grasp_orientation_rpy, degrees=False)

    rclpy.init()
    node = VisualTargetProbe(timeout_sec=args.timeout)

    try:
        node.wait_for_messages()
        target = node.grasp_target
        assert target is not None

        object_position = (
            float(target.pose.position.x),
            float(target.pose.position.y),
            float(target.pose.position.z),
        )
        object_quat = (
            float(target.pose.orientation.x),
            float(target.pose.orientation.y),
            float(target.pose.orientation.z),
            float(target.pose.orientation.w),
        )
        object_transform = pose_matrix(object_position, object_quat)

        def derive_pose(offset_xyz):
            grasp_frame_position = (
                offset_xyz[0] - tcp_offset[0],
                offset_xyz[1] - tcp_offset[1],
                offset_xyz[2] - tcp_offset[2],
            )
            grasp_frame_transform = pose_matrix(
                grasp_frame_position,
                tuple(target_rotation.as_quat()),
            )
            hand_transform = multiply_transform(object_transform, invert_transform(grasp_frame_transform))
            return matrix_to_pose(hand_transform)

        grasp_position, grasp_quat, grasp_rpy = derive_pose(grasp_target_offset)
        pregrasp_position, pregrasp_quat, pregrasp_rpy = derive_pose(pregrasp_offset)

        print("visual_target_probe")
        print(f"target frame: {target.header.frame_id}")
        print(f"class/confidence: {target.class_name} / {target.confidence:.3f}")
        print(f"object pose position: {fmt_xyz(object_position)}")
        print(f"object pose orientation: {fmt_quat(object_quat)}")
        print(f"config tcp_offset_xyz: {fmt_xyz(tcp_offset)}")
        print(f"config grasp_target_offset_xyz: {fmt_xyz(grasp_target_offset)}")
        print(f"config pregrasp_offset_xyz: {fmt_xyz(pregrasp_offset)}")
        print(f"config grasp_orientation_rpy: {fmt_rpy(grasp_orientation_rpy)}")
        print(f"derived grasp pose position: {fmt_xyz(grasp_position)}")
        print(f"derived grasp pose quaternion: {fmt_quat(grasp_quat)}")
        print(f"derived grasp pose rpy: {fmt_rpy(grasp_rpy)}")
        print(f"derived pregrasp pose position: {fmt_xyz(pregrasp_position)}")
        print(f"derived pregrasp pose quaternion: {fmt_quat(pregrasp_quat)}")
        print(f"derived pregrasp pose rpy: {fmt_rpy(pregrasp_rpy)}")

        if node.end_pose is not None:
            end_pose = node.end_pose.pose
            end_quat = (
                float(end_pose.orientation.x),
                float(end_pose.orientation.y),
                float(end_pose.orientation.z),
                float(end_pose.orientation.w),
            )
            end_rpy = tuple(float(v) for v in Rotation.from_quat(end_quat).as_euler("xyz", degrees=False))
            print(f"current end pose position: {fmt_xyz((end_pose.position.x, end_pose.position.y, end_pose.position.z))}")
            print(f"current end pose quaternion: {fmt_quat(end_quat)}")
            print(f"current end pose rpy: {fmt_rpy(end_rpy)}")

        if args.publish != "none":
            publish_position = grasp_position if args.publish == "grasp" else pregrasp_position
            publish_rpy = grasp_rpy if args.publish == "grasp" else pregrasp_rpy
            node.publish_pos_cmd(publish_position, publish_rpy, args.gripper_open_m)
            for _ in range(5):
                rclpy.spin_once(node, timeout_sec=0.05)
                node.publish_pos_cmd(publish_position, publish_rpy, args.gripper_open_m)
            print(f"published {args.publish} pose to /pos_cmd")

    except Exception as exc:
        print(f"visual_target_probe failed: {exc}", file=sys.stderr)
        return 1
    finally:
        node.destroy_node()
        rclpy.shutdown()

    return 0


if __name__ == "__main__":
    sys.exit(main())
