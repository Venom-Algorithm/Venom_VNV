#!/usr/bin/env python3

import argparse
import sys
import time
from typing import Iterable, List

import rclpy
from rcl_interfaces.msg import ParameterType
from rcl_interfaces.srv import GetParameters, SetParameters
from rclpy.action import ActionClient
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.task import Future
from rclpy.utilities import remove_ros_args
from venom_manipulation_interfaces.action import ExecuteTask


def _parse_indices(value: str) -> List[int]:
    indices = [int(item.strip()) for item in value.split(",") if item.strip()]
    if not indices:
        raise argparse.ArgumentTypeError("at least one place index is required")
    return indices


class RepeatVisualPick(Node):
    def __init__(self, args: argparse.Namespace) -> None:
        super().__init__("repeat_visual_pick")
        self.args = args
        self.action_client = ActionClient(self, ExecuteTask, args.action_name)
        self.pick_param_client = self.create_client(
            SetParameters,
            f"{args.pick_node}/set_parameters",
        )
        self.fusion_param_client = self.create_client(
            SetParameters,
            f"{args.fusion_node}/set_parameters",
        )
        self.fusion_get_client = self.create_client(
            GetParameters,
            f"{args.fusion_node}/get_parameters",
        )

    def run(self) -> bool:
        if not self._wait_for_service(self.pick_param_client, "pick parameter service"):
            return False
        if not self._wait_for_service(self.fusion_param_client, "fusion parameter service"):
            return False
        if not self._wait_for_service(self.fusion_get_client, "fusion get-parameter service"):
            return False
        if not self.action_client.wait_for_server(timeout_sec=self.args.wait_timeout_sec):
            self.get_logger().error(
                f"Timed out waiting for action server {self.args.action_name}"
            )
            return False

        if not self._set_string_param(
            self.fusion_param_client,
            "target_class",
            self.args.target_class,
            "fusion target class",
        ):
            return False

        for pick_number, place_index in enumerate(self.args.place_indices, start=1):
            self.get_logger().info(
                f"Starting visual pick {pick_number}/{len(self.args.place_indices)}: "
                f"target='{self.args.target_class}', place_index={place_index}"
            )
            if not self._set_int_param(
                self.pick_param_client,
                "place_target.fixed_pose_index",
                place_index,
                "fixed place index",
            ):
                return False
            if not self._wait_for_fusion_target(self.args.target_class):
                return False
            if not self._send_pick_goal(pick_number):
                return False
            if pick_number != len(self.args.place_indices):
                time.sleep(max(0.0, self.args.delay_between_picks_sec))

        self.get_logger().info("Repeat visual pick sequence completed.")
        return True

    def _wait_for_service(self, client, label: str) -> bool:
        if client.wait_for_service(timeout_sec=self.args.wait_timeout_sec):
            return True
        self.get_logger().error(f"Timed out waiting for {label}")
        return False

    def _set_string_param(self, client, name: str, value: str, label: str) -> bool:
        parameter = Parameter(name, Parameter.Type.STRING, value).to_parameter_msg()
        return self._set_param(client, parameter, label)

    def _set_int_param(self, client, name: str, value: int, label: str) -> bool:
        parameter = Parameter(name, Parameter.Type.INTEGER, value).to_parameter_msg()
        return self._set_param(client, parameter, label)

    def _set_param(self, client, parameter, label: str) -> bool:
        request = SetParameters.Request()
        request.parameters = [parameter]
        future = client.call_async(request)
        if not self._spin_until(future, self.args.wait_timeout_sec):
            self.get_logger().error(f"Timed out setting {label}")
            return False
        results = future.result().results
        if not results or not results[0].successful:
            reason = results[0].reason if results else "no result returned"
            self.get_logger().error(f"Failed to set {label}: {reason}")
            return False
        return True

    def _wait_for_fusion_target(self, expected: str) -> bool:
        deadline = time.monotonic() + max(0.0, self.args.wait_timeout_sec)
        while time.monotonic() < deadline:
            request = GetParameters.Request()
            request.names = ["target_class"]
            future = self.fusion_get_client.call_async(request)
            if self._spin_until(future, 1.0):
                values = future.result().values
                if values and values[0].type == ParameterType.PARAMETER_STRING:
                    if values[0].string_value == expected:
                        return True
            time.sleep(0.1)
        self.get_logger().error(
            f"Fusion target_class did not settle to '{expected}' before timeout"
        )
        return False

    def _send_pick_goal(self, pick_number: int) -> bool:
        goal = ExecuteTask.Goal()
        goal.task_type = ExecuteTask.Goal.PICK_AND_PLACE_LATEST_TARGET
        future = self.action_client.send_goal_async(
            goal,
            feedback_callback=lambda feedback: self.get_logger().info(
                f"pick {pick_number}: {feedback.feedback.message}"
            ),
        )
        if not self._spin_until(future, self.args.wait_timeout_sec):
            self.get_logger().error("Timed out sending visual pick goal")
            return False

        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error("Visual pick goal was rejected")
            return False

        result_future = goal_handle.get_result_async()
        if not self._spin_until(result_future, self.args.goal_timeout_sec):
            self.get_logger().error("Timed out waiting for visual pick result")
            return False

        result = result_future.result().result
        if not result.success:
            self.get_logger().error(
                f"Visual pick failed: stage={result.stage_reached} "
                f"error={result.error_code} message='{result.message}'"
            )
            return False
        self.get_logger().info(f"Visual pick succeeded: {result.message}")
        return True

    def _spin_until(self, future: Future, timeout_sec: float) -> bool:
        rclpy.spin_until_future_complete(self, future, timeout_sec=timeout_sec)
        return future.done()


def main(argv: Iterable[str] = sys.argv[1:]) -> int:
    ros_stripped_argv = remove_ros_args(args=list(argv))
    parser = argparse.ArgumentParser()
    parser.add_argument("--action-name", default="/manipulation/execute_task")
    parser.add_argument("--pick-node", default="/pick_place_server")
    parser.add_argument("--fusion-node", default="/grasp_target_fusion")
    parser.add_argument("--target-class", default="bottle")
    parser.add_argument("--place-indices", type=_parse_indices, default=[0, 1])
    parser.add_argument("--wait-timeout-sec", type=float, default=60.0)
    parser.add_argument("--goal-timeout-sec", type=float, default=180.0)
    parser.add_argument("--delay-between-picks-sec", type=float, default=1.0)
    args = parser.parse_args(ros_stripped_argv)

    rclpy.init()
    node = RepeatVisualPick(args)
    try:
        return 0 if node.run() else 1
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
