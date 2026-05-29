#!/usr/bin/env python3
"""Solve eye-in-hand calibration from collected chessboard samples."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np


METHODS = {
    "tsai": cv2.CALIB_HAND_EYE_TSAI,
    "park": cv2.CALIB_HAND_EYE_PARK,
    "horaud": cv2.CALIB_HAND_EYE_HORAUD,
    "andreff": cv2.CALIB_HAND_EYE_ANDREFF,
    "daniilidis": cv2.CALIB_HAND_EYE_DANIILIDIS,
}


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


def matrix_from_rt(rotation: np.ndarray, translation: np.ndarray) -> np.ndarray:
    transform = np.eye(4, dtype=np.float64)
    transform[:3, :3] = rotation
    transform[:3, 3] = translation.reshape(3)
    return transform


def residual_score(
    rotations_gripper2base: list[np.ndarray],
    translations_gripper2base: list[np.ndarray],
    rotations_target2cam: list[np.ndarray],
    translations_target2cam: list[np.ndarray],
    hand_to_camera: np.ndarray,
) -> float:
    if len(rotations_gripper2base) < 2:
        return 0.0

    residuals: list[float] = []
    for first in range(len(rotations_gripper2base) - 1):
        for second in range(first + 1, len(rotations_gripper2base)):
            base_hand_first = matrix_from_rt(
                rotations_gripper2base[first], translations_gripper2base[first]
            )
            base_hand_second = matrix_from_rt(
                rotations_gripper2base[second], translations_gripper2base[second]
            )
            target_cam_first = matrix_from_rt(
                rotations_target2cam[first], translations_target2cam[first]
            )
            target_cam_second = matrix_from_rt(
                rotations_target2cam[second], translations_target2cam[second]
            )

            motion_hand = np.linalg.inv(base_hand_second) @ base_hand_first
            motion_target = target_cam_second @ np.linalg.inv(target_cam_first)
            lhs = motion_hand @ hand_to_camera
            rhs = hand_to_camera @ motion_target
            residuals.append(float(np.linalg.norm(lhs - rhs, ord="fro")))
    return float(np.mean(residuals))


def solve_method(
    method_name: str,
    rotations_gripper2base: list[np.ndarray],
    translations_gripper2base: list[np.ndarray],
    rotations_target2cam: list[np.ndarray],
    translations_target2cam: list[np.ndarray],
) -> tuple[np.ndarray, np.ndarray, float]:
    rotation_cam2gripper, translation_cam2gripper = cv2.calibrateHandEye(
        rotations_gripper2base,
        translations_gripper2base,
        rotations_target2cam,
        translations_target2cam,
        method=METHODS[method_name],
    )
    translation_cam2gripper = translation_cam2gripper.reshape(3)
    transform = matrix_from_rt(rotation_cam2gripper, translation_cam2gripper)
    residual = residual_score(
        rotations_gripper2base,
        translations_gripper2base,
        rotations_target2cam,
        translations_target2cam,
        transform,
    )
    return rotation_cam2gripper, translation_cam2gripper, residual


def write_yaml(path: Path, parent_frame: str, child_frame: str, translation: np.ndarray, quaternion: list[float]) -> None:
    payload = (
        "handeye:\n"
        "  ros__parameters:\n"
        f"    parent_frame: {parent_frame}\n"
        f"    child_frame: {child_frame}\n"
        f"    translation_xyz: [{translation[0]:.9f}, {translation[1]:.9f}, {translation[2]:.9f}]\n"
        f"    rotation_xyzw: [{quaternion[0]:.9f}, {quaternion[1]:.9f}, {quaternion[2]:.9f}, {quaternion[3]:.9f}]\n"
    )
    path.write_text(payload, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("/tmp/handeye_chessboard_samples.json"))
    parser.add_argument("--method", choices=["best", *METHODS.keys()], default="best")
    parser.add_argument(
        "--output-yaml",
        type=Path,
        default=Path("perception/grasp_target_fusion/handeye/hand_to_camera_optical_frame_2026-05-13.yaml"),
    )
    parser.add_argument("--parent-frame", help="Override the parent frame written to YAML.")
    parser.add_argument("--child-frame", help="Override the child frame written to YAML.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    samples = payload.get("samples", [])
    if len(samples) < 5:
        raise SystemExit("Need at least 5 samples to solve hand-eye calibration.")

    rotations_gripper2base: list[np.ndarray] = []
    translations_gripper2base: list[np.ndarray] = []
    rotations_target2cam: list[np.ndarray] = []
    translations_target2cam: list[np.ndarray] = []

    for sample in samples:
        rotations_gripper2base.append(
            quaternion_xyzw_to_rotation_matrix(sample["q_base_hand_xyzw"])
        )
        translations_gripper2base.append(np.array(sample["t_base_hand"], dtype=np.float64).reshape(3, 1))
        rotations_target2cam.append(
            quaternion_xyzw_to_rotation_matrix(sample["q_target_camera_xyzw"])
        )
        translations_target2cam.append(np.array(sample["t_target_camera"], dtype=np.float64).reshape(3, 1))

    method_names = list(METHODS.keys()) if args.method == "best" else [args.method]
    solved: list[tuple[str, np.ndarray, np.ndarray, float]] = []
    for method_name in method_names:
        try:
            rotation, translation, residual = solve_method(
                method_name,
                rotations_gripper2base,
                translations_gripper2base,
                rotations_target2cam,
                translations_target2cam,
            )
            solved.append((method_name, rotation, translation, residual))
        except cv2.error as exc:
            print(f"{method_name}: OpenCV solve failed: {exc}")

    if not solved:
        raise SystemExit("No hand-eye solution could be computed from the provided samples.")

    solved.sort(key=lambda item: item[3])
    print("Hand-eye solutions (lower residual is better):")
    for method_name, rotation, translation, residual in solved:
        quaternion = rotation_matrix_to_quaternion_xyzw(rotation)
        print(
            f"  {method_name:10s} residual={residual:.6f} "
            f"t=[{translation[0]:.4f}, {translation[1]:.4f}, {translation[2]:.4f}] "
            f"q=[{quaternion[0]:.5f}, {quaternion[1]:.5f}, {quaternion[2]:.5f}, {quaternion[3]:.5f}]"
        )

    best_method, best_rotation, best_translation, _ = solved[0]
    best_quaternion = rotation_matrix_to_quaternion_xyzw(best_rotation)
    parent_frame = args.parent_frame or payload["hand_frame"]
    child_frame = args.child_frame or payload["camera_frame"]
    write_yaml(args.output_yaml, parent_frame, child_frame, best_translation, best_quaternion)
    print(f"Selected method: {best_method}")
    print(f"Wrote YAML to {args.output_yaml}")


if __name__ == "__main__":
    main()
