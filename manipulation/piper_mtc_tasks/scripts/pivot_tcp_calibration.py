#!/usr/bin/env python3
"""Pivot-calibrate a Piper TCP translation from TF samples.

The operator touches the same fixed physical point with the same physical
tool tip from several wrist orientations.  For each sample:

    target_base = R_base_tool * tcp_tool + t_base_tool

The script solves tcp_tool and target_base with least squares.
"""

import argparse
import json
import math
import threading
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import rclpy
from rclpy.duration import Duration
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from rclpy.time import Time
import tf2_ros


@dataclass
class TransformSample:
    stamp_sec: float
    translation: np.ndarray
    quaternion_xyzw: np.ndarray


def quaternion_to_matrix_xyzw(quaternion: np.ndarray) -> np.ndarray:
    x, y, z, w = quaternion
    norm = math.sqrt(x * x + y * y + z * z + w * w)
    if norm == 0.0:
        raise ValueError("Quaternion norm is zero")

    x /= norm
    y /= norm
    z /= norm
    w /= norm

    return np.array(
        [
            [1.0 - 2.0 * (y * y + z * z), 2.0 * (x * y - z * w), 2.0 * (x * z + y * w)],
            [2.0 * (x * y + z * w), 1.0 - 2.0 * (x * x + z * z), 2.0 * (y * z - x * w)],
            [2.0 * (x * z - y * w), 2.0 * (y * z + x * w), 1.0 - 2.0 * (x * x + y * y)],
        ],
        dtype=float,
    )


def sample_to_json(sample: TransformSample) -> dict:
    return {
        "stamp_sec": sample.stamp_sec,
        "translation": sample.translation.tolist(),
        "quaternion_xyzw": sample.quaternion_xyzw.tolist(),
    }


def sample_from_json(data: dict) -> TransformSample:
    return TransformSample(
        stamp_sec=float(data["stamp_sec"]),
        translation=np.array(data["translation"], dtype=float),
        quaternion_xyzw=np.array(data["quaternion_xyzw"], dtype=float),
    )


def solve_pivot(samples: list[TransformSample]) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    if len(samples) < 3:
        raise ValueError("At least 3 samples are required; 5 or more is recommended")

    rows = []
    rhs = []
    for sample in samples:
        rotation = quaternion_to_matrix_xyzw(sample.quaternion_xyzw)
        rows.append(np.hstack((rotation, -np.eye(3))))
        rhs.append(-sample.translation)

    matrix = np.vstack(rows)
    vector = np.concatenate(rhs)
    solution, _, _, singular_values = np.linalg.lstsq(matrix, vector, rcond=None)
    tcp_tool = solution[:3]
    target_base = solution[3:]

    residuals = []
    for sample in samples:
        rotation = quaternion_to_matrix_xyzw(sample.quaternion_xyzw)
        residuals.append(np.linalg.norm(rotation @ tcp_tool + sample.translation - target_base))

    condition = float(singular_values[0] / singular_values[-1]) if singular_values[-1] > 0.0 else math.inf
    return tcp_tool, target_base, np.array(residuals), condition


def format_vector(values: np.ndarray) -> str:
    return "[" + ", ".join(f"{value:.6f}" for value in values.tolist()) + "]"


def print_solution(samples: list[TransformSample]) -> None:
    tcp_tool, target_base, residuals, condition = solve_pivot(samples)
    print()
    print("Pivot calibration result")
    print(f"  samples: {len(samples)}")
    print(f"  tcp in tool frame: {format_vector(tcp_tool)}")
    print(f"  touched point in base frame: {format_vector(target_base)}")
    print(f"  residuals m: {format_vector(residuals)}")
    print(f"  rms residual m: {math.sqrt(float(np.mean(residuals * residuals))):.6f}")
    print(f"  max residual m: {float(np.max(residuals)):.6f}")
    print(f"  least-squares condition: {condition:.2f}")
    print()
    print("Suggested MTC YAML values if hand_frame is the sampled tool frame:")
    print(f"  tcp_offset_xyz: {format_vector(tcp_tool)}")
    print("  pregrasp_offset_xyz: [0.000000, 0.000000, 0.000000]")
    print()
    print("Notes:")
    print("  - This solves TCP translation only, not TCP orientation.")
    print("  - If max residual is above 0.003 m, retake samples with more varied wrist orientations.")
    print("  - If residual is good but grasp still fails, calibrate/define a real tool_tip frame in URDF.")


class TfSampler(Node):
    def __init__(self, base_frame: str, tool_frame: str, timeout_sec: float) -> None:
        super().__init__("pivot_tcp_calibration")
        self.base_frame = base_frame
        self.tool_frame = tool_frame
        self.timeout = Duration(seconds=timeout_sec)
        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)

    def capture(self) -> TransformSample:
        transform = self.tf_buffer.lookup_transform(
            self.base_frame,
            self.tool_frame,
            Time(),
            timeout=self.timeout,
        )
        translation = transform.transform.translation
        rotation = transform.transform.rotation
        stamp = transform.header.stamp
        return TransformSample(
            stamp_sec=float(stamp.sec) + float(stamp.nanosec) * 1e-9,
            translation=np.array([translation.x, translation.y, translation.z], dtype=float),
            quaternion_xyzw=np.array([rotation.x, rotation.y, rotation.z, rotation.w], dtype=float),
        )


def save_samples(path: Path, base_frame: str, tool_frame: str, samples: list[TransformSample]) -> None:
    payload = {
        "base_frame": base_frame,
        "tool_frame": tool_frame,
        "samples": [sample_to_json(sample) for sample in samples],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Saved {len(samples)} samples to {path}")


def load_samples(path: Path) -> tuple[str, str, list[TransformSample]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return (
        payload.get("base_frame", ""),
        payload.get("tool_frame", ""),
        [sample_from_json(sample) for sample in payload["samples"]],
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-frame", default="base_link")
    parser.add_argument("--tool-frame", default="gripper_base")
    parser.add_argument("--timeout-sec", type=float, default=1.0)
    parser.add_argument("--save", type=Path, default=Path("/tmp/piper_tcp_pivot_samples.json"))
    parser.add_argument("--load", type=Path, help="Solve from a previously saved JSON sample file")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.load:
        base_frame, tool_frame, samples = load_samples(args.load)
        print(f"Loaded {len(samples)} samples from {args.load}")
        if base_frame or tool_frame:
            print(f"Frames in file: base={base_frame}, tool={tool_frame}")
        print_solution(samples)
        return

    rclpy.init()
    node = TfSampler(args.base_frame, args.tool_frame, args.timeout_sec)
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    spin_thread = threading.Thread(target=executor.spin, daemon=True)
    spin_thread.start()

    samples: list[TransformSample] = []
    print("Pivot TCP calibration")
    print(f"  base frame: {args.base_frame}")
    print(f"  tool frame: {args.tool_frame}")
    print("Commands:")
    print("  Enter : capture current TF sample")
    print("  s     : solve with current samples")
    print("  d     : delete last sample")
    print("  w     : save samples")
    print("  q     : quit")

    try:
        while rclpy.ok():
            command = input("sample> ").strip().lower()
            if command == "q":
                break
            if command == "d":
                if samples:
                    samples.pop()
                    print(f"Deleted last sample. Remaining: {len(samples)}")
                else:
                    print("No samples to delete.")
                continue
            if command == "w":
                save_samples(args.save, args.base_frame, args.tool_frame, samples)
                continue
            if command == "s":
                try:
                    print_solution(samples)
                except ValueError as error:
                    print(f"Cannot solve: {error}")
                continue
            if command:
                print("Unknown command. Use Enter, s, d, w, or q.")
                continue

            try:
                sample = node.capture()
            except Exception as error:  # noqa: BLE001 - CLI tool should show TF lookup errors.
                print(f"Failed to capture TF: {error}")
                continue

            samples.append(sample)
            print(
                f"Captured #{len(samples)}: "
                f"t={format_vector(sample.translation)}, "
                f"q_xyzw={format_vector(sample.quaternion_xyzw)}"
            )
    finally:
        save_samples(args.save, args.base_frame, args.tool_frame, samples)
        executor.shutdown()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
