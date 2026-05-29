#!/usr/bin/env python3
"""Collect eye-in-hand calibration samples from a chessboard target.

This tool captures synchronized:
  - base -> hand TF samples
  - target(board) -> camera PnP solutions

It is designed for an eye-in-hand setup where the camera is rigidly mounted on
the manipulator and the chessboard remains stationary during data collection.
"""

from __future__ import annotations

import argparse
import json
import threading
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
import rclpy
from rclpy.duration import Duration
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from sensor_msgs.msg import CameraInfo, Image
from tf2_ros import Buffer, TransformException, TransformListener


def rotation_matrix_to_quaternion_xyzw(rotation: np.ndarray) -> list[float]:
    trace = float(np.trace(rotation))
    if trace > 0.0:
        s = 0.5 / np.sqrt(trace + 1.0)
        w = 0.25 / s
        x = (rotation[2, 1] - rotation[1, 2]) * s
        y = (rotation[0, 2] - rotation[2, 0]) * s
        z = (rotation[1, 0] - rotation[0, 1]) * s
    else:
        if rotation[0, 0] > rotation[1, 1] and rotation[0, 0] > rotation[2, 2]:
            s = 2.0 * np.sqrt(1.0 + rotation[0, 0] - rotation[1, 1] - rotation[2, 2])
            w = (rotation[2, 1] - rotation[1, 2]) / s
            x = 0.25 * s
            y = (rotation[0, 1] + rotation[1, 0]) / s
            z = (rotation[0, 2] + rotation[2, 0]) / s
        elif rotation[1, 1] > rotation[2, 2]:
            s = 2.0 * np.sqrt(1.0 + rotation[1, 1] - rotation[0, 0] - rotation[2, 2])
            w = (rotation[0, 2] - rotation[2, 0]) / s
            x = (rotation[0, 1] + rotation[1, 0]) / s
            y = 0.25 * s
            z = (rotation[1, 2] + rotation[2, 1]) / s
        else:
            s = 2.0 * np.sqrt(1.0 + rotation[2, 2] - rotation[0, 0] - rotation[1, 1])
            w = (rotation[1, 0] - rotation[0, 1]) / s
            x = (rotation[0, 2] + rotation[2, 0]) / s
            y = (rotation[1, 2] + rotation[2, 1]) / s
            z = 0.25 * s
    quaternion = np.array([x, y, z, w], dtype=np.float64)
    quaternion /= np.linalg.norm(quaternion)
    return quaternion.tolist()


def quaternion_xyzw_to_rotation_matrix(quaternion: list[float]) -> np.ndarray:
    x, y, z, w = quaternion
    xx, yy, zz = x * x, y * y, z * z
    xy, xz, yz = x * y, x * z, y * z
    wx, wy, wz = w * x, w * y, w * z
    return np.array(
        [
            [1.0 - 2.0 * (yy + zz), 2.0 * (xy - wz), 2.0 * (xz + wy)],
            [2.0 * (xy + wz), 1.0 - 2.0 * (xx + zz), 2.0 * (yz - wx)],
            [2.0 * (xz - wy), 2.0 * (yz + wx), 1.0 - 2.0 * (xx + yy)],
        ],
        dtype=np.float64,
    )


def image_message_to_bgr(image: Image) -> np.ndarray:
    if image.encoding == "bgr8":
        return np.frombuffer(image.data, dtype=np.uint8).reshape(image.height, image.width, 3).copy()
    if image.encoding == "rgb8":
        rgb = np.frombuffer(image.data, dtype=np.uint8).reshape(image.height, image.width, 3)
        return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    if image.encoding == "mono8":
        mono = np.frombuffer(image.data, dtype=np.uint8).reshape(image.height, image.width)
        return cv2.cvtColor(mono, cv2.COLOR_GRAY2BGR)
    raise ValueError(f"Unsupported image encoding '{image.encoding}' for hand-eye sampling")


@dataclass
class BoardConfig:
    cols: int
    rows: int
    square_size_m: float


@dataclass
class SampleRecord:
    timestamp_ns: int
    image_frame: str
    board_cols: int
    board_rows: int
    square_size_m: float
    reprojection_error_px: float
    t_base_hand: list[float]
    q_base_hand_xyzw: list[float]
    t_target_camera: list[float]
    q_target_camera_xyzw: list[float]


class HandEyeSampleCollector(Node):
    def __init__(
        self,
        image_topic: str,
        camera_info_topic: str,
        base_frame: str,
        hand_frame: str,
        board: BoardConfig,
        timeout_sec: float,
    ) -> None:
        super().__init__("handeye_sample_collector")
        self.image_topic = image_topic
        self.camera_info_topic = camera_info_topic
        self.base_frame = base_frame
        self.hand_frame = hand_frame
        self.board = board
        self.timeout_sec = timeout_sec
        self.camera_info: Optional[CameraInfo] = None
        self.latest_image: Optional[Image] = None
        self.lock = threading.Lock()
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        self.object_points = self._build_object_points()

        self.create_subscription(CameraInfo, camera_info_topic, self._camera_info_callback, 10)
        self.create_subscription(Image, image_topic, self._image_callback, 10)

    def _build_object_points(self) -> np.ndarray:
        object_points = np.zeros((self.board.rows * self.board.cols, 3), dtype=np.float32)
        grid = np.mgrid[0 : self.board.cols, 0 : self.board.rows].T.reshape(-1, 2)
        object_points[:, :2] = grid * self.board.square_size_m
        return object_points

    def _camera_info_callback(self, message: CameraInfo) -> None:
        with self.lock:
            self.camera_info = message

    def _image_callback(self, message: Image) -> None:
        with self.lock:
            self.latest_image = message

    def capture_sample(self) -> SampleRecord:
        with self.lock:
            camera_info = self.camera_info
            image = self.latest_image

        if camera_info is None:
            raise RuntimeError("CameraInfo has not been received yet.")
        if image is None:
            raise RuntimeError("Image has not been received yet.")

        transform = self.tf_buffer.lookup_transform(
            self.base_frame,
            self.hand_frame,
            rclpy.time.Time(),
            timeout=Duration(seconds=self.timeout_sec),
        )

        bgr = image_message_to_bgr(image)
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        pattern_size = (self.board.cols, self.board.rows)

        found, corners = cv2.findChessboardCornersSB(gray, pattern_size)
        if not found or corners is None:
            found, corners = cv2.findChessboardCorners(
                gray,
                pattern_size,
                cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_NORMALIZE_IMAGE,
            )
            if found and corners is not None:
                termination = (
                    cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER,
                    30,
                    0.001,
                )
                corners = cv2.cornerSubPix(gray, corners, (5, 5), (-1, -1), termination)

        if not found or corners is None:
            raise RuntimeError("Chessboard not detected in the latest color image.")

        camera_matrix = np.array(camera_info.k, dtype=np.float64).reshape(3, 3)
        distortion = np.array(camera_info.d, dtype=np.float64)
        success, rvec, tvec = cv2.solvePnP(
            self.object_points,
            corners,
            camera_matrix,
            distortion,
            flags=cv2.SOLVEPNP_ITERATIVE,
        )
        if not success:
            raise RuntimeError("solvePnP failed for the detected chessboard.")

        projected, _ = cv2.projectPoints(self.object_points, rvec, tvec, camera_matrix, distortion)
        reprojection_error = float(
            np.mean(np.linalg.norm(projected.reshape(-1, 2) - corners.reshape(-1, 2), axis=1))
        )

        rotation_matrix, _ = cv2.Rodrigues(rvec)
        q_target_camera = rotation_matrix_to_quaternion_xyzw(rotation_matrix)

        t_base_hand = [
            float(transform.transform.translation.x),
            float(transform.transform.translation.y),
            float(transform.transform.translation.z),
        ]
        q_base_hand = [
            float(transform.transform.rotation.x),
            float(transform.transform.rotation.y),
            float(transform.transform.rotation.z),
            float(transform.transform.rotation.w),
        ]
        timestamp_ns = int(self.get_clock().now().nanoseconds)

        return SampleRecord(
            timestamp_ns=timestamp_ns,
            image_frame=image.header.frame_id or camera_info.header.frame_id,
            board_cols=self.board.cols,
            board_rows=self.board.rows,
            square_size_m=self.board.square_size_m,
            reprojection_error_px=reprojection_error,
            t_base_hand=t_base_hand,
            q_base_hand_xyzw=q_base_hand,
            t_target_camera=[float(v) for v in tvec.reshape(3)],
            q_target_camera_xyzw=q_target_camera,
        )


def save_samples(
    path: Path,
    base_frame: str,
    hand_frame: str,
    camera_frame: str,
    image_topic: str,
    camera_info_topic: str,
    board: BoardConfig,
    samples: list[SampleRecord],
) -> None:
    payload = {
        "base_frame": base_frame,
        "hand_frame": hand_frame,
        "camera_frame": camera_frame,
        "image_topic": image_topic,
        "camera_info_topic": camera_info_topic,
        "board": asdict(board),
        "samples": [asdict(sample) for sample in samples],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image-topic", default="/camera/d435i/color/image_raw")
    parser.add_argument("--camera-info-topic", default="/camera/d435i/color/camera_info")
    parser.add_argument("--base-frame", default="piper_base_link")
    parser.add_argument("--hand-frame", default="piper_gripper_base")
    parser.add_argument("--board-cols", type=int, default=10)
    parser.add_argument("--board-rows", type=int, default=8)
    parser.add_argument("--square-size-mm", type=float, default=15.0)
    parser.add_argument("--timeout-sec", type=float, default=1.0)
    parser.add_argument("--save", type=Path, default=Path("/tmp/handeye_chessboard_samples.json"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    board = BoardConfig(
        cols=args.board_cols,
        rows=args.board_rows,
        square_size_m=args.square_size_mm / 1000.0,
    )

    rclpy.init()
    node = HandEyeSampleCollector(
        image_topic=args.image_topic,
        camera_info_topic=args.camera_info_topic,
        base_frame=args.base_frame,
        hand_frame=args.hand_frame,
        board=board,
        timeout_sec=args.timeout_sec,
    )
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    spin_thread = threading.Thread(target=executor.spin, daemon=True)
    spin_thread.start()

    samples: list[SampleRecord] = []
    print("Chessboard hand-eye sample collector")
    print(f"  image topic : {args.image_topic}")
    print(f"  camera info : {args.camera_info_topic}")
    print(f"  base frame  : {args.base_frame}")
    print(f"  hand frame  : {args.hand_frame}")
    print(f"  board       : {args.board_cols}x{args.board_rows} inner corners, {args.square_size_mm:.3f} mm")
    print("Commands:")
    print("  Enter : capture current sample")
    print("  d     : delete last sample")
    print("  w     : write sample file")
    print("  q     : quit")

    try:
        while rclpy.ok():
            command = input("> ").strip().lower()
            if command == "":
                try:
                    sample = node.capture_sample()
                except TransformException as exc:
                    print(f"TF lookup failed: {exc}")
                    continue
                except RuntimeError as exc:
                    print(f"Capture failed: {exc}")
                    continue

                samples.append(sample)
                print(
                    f"Captured sample #{len(samples)} "
                    f"(reprojection error {sample.reprojection_error_px:.3f}px, "
                    f"frame {sample.image_frame})"
                )
            elif command == "d":
                if samples:
                    samples.pop()
                    print(f"Deleted last sample. Remaining: {len(samples)}")
                else:
                    print("No samples to delete.")
            elif command == "w":
                camera_frame = samples[-1].image_frame if samples else ""
                save_samples(
                    args.save,
                    args.base_frame,
                    args.hand_frame,
                    camera_frame,
                    args.image_topic,
                    args.camera_info_topic,
                    board,
                    samples,
                )
                print(f"Wrote {len(samples)} samples to {args.save}")
            elif command == "q":
                break
            else:
                print("Unknown command. Use Enter, d, w, or q.")
    finally:
        if samples:
            camera_frame = samples[-1].image_frame
            save_samples(
                args.save,
                args.base_frame,
                args.hand_frame,
                camera_frame,
                args.image_topic,
                args.camera_info_topic,
                board,
                samples,
            )
            print(f"Auto-saved {len(samples)} samples to {args.save}")
        executor.shutdown()
        node.destroy_node()
        rclpy.shutdown()
        spin_thread.join(timeout=1.0)


if __name__ == "__main__":
    main()
