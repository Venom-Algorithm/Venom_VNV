import math
from typing import Dict, List, Optional

from geometry_msgs.msg import Twist
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CameraInfo, JointState
from std_msgs.msg import String
from std_srvs.srv import SetBool
from venom_manipulation_interfaces.msg import Detection2D, Detection2DArray


class FlameArmTracker(Node):
    def __init__(self) -> None:
        super().__init__("flame_arm_tracker")

        self.declare_parameter("detection_array_topic", "/perception/detections_2d_array")
        self.declare_parameter("camera_info_topic", "/camera/d435i/color/camera_info")
        self.declare_parameter("joint_state_topic", "/joint_states")
        self.declare_parameter("cmd_vel_topic", "/cmd_vel")
        self.declare_parameter("joint_command_topic", "/joint_command")
        self.declare_parameter("debug_topic", "/flame_arm_tracker/debug")
        self.declare_parameter("target_class_name", "flame_picture")
        self.declare_parameter("command_rate_hz", 30.0)
        self.declare_parameter("tracking_timeout_sec", 0.30)
        self.declare_parameter("lost_target_prediction_start_sec", 0.10)
        self.declare_parameter("lost_target_prediction_speed_scale", 0.55)
        self.declare_parameter("joint_state_timeout_sec", 0.30)
        self.declare_parameter("observe_duration_sec", 2.0)
        self.declare_parameter("observe_position_tolerance_rad", 0.05)
        self.declare_parameter("command_velocity", 40.0)
        self.declare_parameter("kp_yaw", 0.70)
        self.declare_parameter("kd_yaw", 0.0)
        self.declare_parameter("kp_pitch", 0.45)
        self.declare_parameter("kd_pitch", 0.0)
        self.declare_parameter("cmd_vel_yaw_feedforward_gain", 1.0)
        self.declare_parameter("deadband_rad", 0.010)
        self.declare_parameter("deadband_hysteresis_rad", 0.0)
        self.declare_parameter("target_center_offset_x_px", 0.0)
        self.declare_parameter("target_center_offset_y_px", 0.0)
        self.declare_parameter("min_consecutive_detections", 3)
        self.declare_parameter("max_detection_jump_px", 180.0)
        self.declare_parameter("target_smoothing_alpha", 0.35)
        self.declare_parameter("use_alpha_beta_filter", True)
        self.declare_parameter("alpha_beta_alpha", 0.65)
        self.declare_parameter("alpha_beta_beta", 0.10)
        self.declare_parameter("target_prediction_sec", 0.08)
        self.declare_parameter("derivative_filter_alpha", 0.25)
        self.declare_parameter("use_dual_loop_yaw", True)
        self.declare_parameter("outer_kp_yaw", 1.20)
        self.declare_parameter("outer_kd_yaw", 0.06)
        self.declare_parameter("inner_kp_yaw_velocity", 0.35)
        self.declare_parameter("inner_ki_yaw_velocity", 0.0)
        self.declare_parameter("max_yaw_velocity_rad_s", 0.50)
        self.declare_parameter("max_yaw_accel_rad_s2", 1.80)
        self.declare_parameter("max_yaw_velocity_integral", 0.30)
        self.declare_parameter("use_command_accumulator", False)
        self.declare_parameter("max_command_feedback_lead", 0.06)
        self.declare_parameter("yaw_joint_sign", 1.0)
        self.declare_parameter("pitch_joint5_sign", 1.0)
        self.declare_parameter("pitch_joint6_sign", 0.35)
        self.declare_parameter("observe_joints", [0.0, 0.95, -1.45, 0.0, 0.55, 0.0])
        self.declare_parameter("joint_delta_limits", [0.015, 0.0, 0.0, 0.0, 0.010, 0.010])
        self.declare_parameter("joint_min_limits", [-2.60, -0.10, -2.60, -2.80, -1.60, -2.80])
        self.declare_parameter("joint_max_limits", [2.60, 2.30, 0.20, 2.80, 1.60, 2.80])

        self.target_class_name = str(self.get_parameter("target_class_name").value)
        self.command_rate_hz = max(1.0, float(self.get_parameter("command_rate_hz").value))
        self.tracking_timeout_sec = float(self.get_parameter("tracking_timeout_sec").value)
        self.lost_target_prediction_start_sec = max(
            0.0,
            float(self.get_parameter("lost_target_prediction_start_sec").value),
        )
        self.lost_target_prediction_speed_scale = max(
            0.0,
            min(1.0, float(self.get_parameter("lost_target_prediction_speed_scale").value)),
        )
        self.joint_state_timeout_sec = float(self.get_parameter("joint_state_timeout_sec").value)
        self.observe_duration_sec = max(0.1, float(self.get_parameter("observe_duration_sec").value))
        self.observe_position_tolerance_rad = max(
            0.0,
            float(self.get_parameter("observe_position_tolerance_rad").value),
        )
        self.command_velocity = float(self.get_parameter("command_velocity").value)
        self.kp_yaw = float(self.get_parameter("kp_yaw").value)
        self.kd_yaw = float(self.get_parameter("kd_yaw").value)
        self.kp_pitch = float(self.get_parameter("kp_pitch").value)
        self.kd_pitch = float(self.get_parameter("kd_pitch").value)
        self.cmd_vel_yaw_feedforward_gain = float(
            self.get_parameter("cmd_vel_yaw_feedforward_gain").value
        )
        self.deadband_rad = float(self.get_parameter("deadband_rad").value)
        self.deadband_hysteresis_rad = max(
            0.0,
            float(self.get_parameter("deadband_hysteresis_rad").value),
        )
        self.target_center_offset_x_px = float(
            self.get_parameter("target_center_offset_x_px").value
        )
        self.target_center_offset_y_px = float(
            self.get_parameter("target_center_offset_y_px").value
        )
        self.min_consecutive_detections = max(
            1,
            int(self.get_parameter("min_consecutive_detections").value),
        )
        self.max_detection_jump_px = max(
            0.0,
            float(self.get_parameter("max_detection_jump_px").value),
        )
        self.target_smoothing_alpha = max(
            0.0,
            min(1.0, float(self.get_parameter("target_smoothing_alpha").value)),
        )
        self.use_alpha_beta_filter = bool(self.get_parameter("use_alpha_beta_filter").value)
        self.alpha_beta_alpha = max(
            0.0,
            min(1.0, float(self.get_parameter("alpha_beta_alpha").value)),
        )
        self.alpha_beta_beta = max(
            0.0,
            min(1.0, float(self.get_parameter("alpha_beta_beta").value)),
        )
        self.target_prediction_sec = max(
            0.0,
            float(self.get_parameter("target_prediction_sec").value),
        )
        self.derivative_filter_alpha = max(
            0.0,
            min(1.0, float(self.get_parameter("derivative_filter_alpha").value)),
        )
        self.use_dual_loop_yaw = bool(self.get_parameter("use_dual_loop_yaw").value)
        self.outer_kp_yaw = float(self.get_parameter("outer_kp_yaw").value)
        self.outer_kd_yaw = float(self.get_parameter("outer_kd_yaw").value)
        self.inner_kp_yaw_velocity = float(self.get_parameter("inner_kp_yaw_velocity").value)
        self.inner_ki_yaw_velocity = float(self.get_parameter("inner_ki_yaw_velocity").value)
        self.max_yaw_velocity_rad_s = abs(
            float(self.get_parameter("max_yaw_velocity_rad_s").value)
        )
        self.max_yaw_accel_rad_s2 = abs(
            float(self.get_parameter("max_yaw_accel_rad_s2").value)
        )
        self.max_yaw_velocity_integral = abs(
            float(self.get_parameter("max_yaw_velocity_integral").value)
        )
        self.use_command_accumulator = bool(self.get_parameter("use_command_accumulator").value)
        self.max_command_feedback_lead = max(
            0.0,
            float(self.get_parameter("max_command_feedback_lead").value),
        )
        self.yaw_joint_sign = float(self.get_parameter("yaw_joint_sign").value)
        self.pitch_joint5_sign = float(self.get_parameter("pitch_joint5_sign").value)
        self.pitch_joint6_sign = float(self.get_parameter("pitch_joint6_sign").value)
        self.observe_joints = self._read_six_float_parameter("observe_joints")
        self.joint_delta_limits = self._read_six_float_parameter("joint_delta_limits")
        self.joint_min_limits = self._read_six_float_parameter("joint_min_limits")
        self.joint_max_limits = self._read_six_float_parameter("joint_max_limits")

        self.command_pub = self.create_publisher(
            JointState,
            str(self.get_parameter("joint_command_topic").value),
            10,
        )
        self.debug_pub = self.create_publisher(
            String,
            str(self.get_parameter("debug_topic").value),
            10,
        )
        self.create_subscription(
            Detection2DArray,
            str(self.get_parameter("detection_array_topic").value),
            self.detections_callback,
            10,
        )
        self.create_subscription(
            CameraInfo,
            str(self.get_parameter("camera_info_topic").value),
            self.camera_info_callback,
            10,
        )
        self.create_subscription(
            JointState,
            str(self.get_parameter("joint_state_topic").value),
            self.joint_state_callback,
            10,
        )
        self.create_subscription(
            Twist,
            str(self.get_parameter("cmd_vel_topic").value),
            self.cmd_vel_callback,
            10,
        )
        self.enable_service = self.create_service(
            SetBool,
            "set_enabled",
            self.set_enabled_callback,
        )

        self.enabled = False
        self.mode = "idle"
        self.latest_detection: Optional[Detection2D] = None
        self.latest_detection_time: Optional[rclpy.time.Time] = None
        self.consecutive_detection_count = 0
        self.latest_camera_info: Optional[CameraInfo] = None
        self.latest_joint_state: Optional[Dict[str, float]] = None
        self.latest_joint_state_time: Optional[rclpy.time.Time] = None
        self.latest_joint_velocity: Optional[Dict[str, float]] = None
        self.latest_cmd_vel = Twist()
        self.observe_start_time: Optional[rclpy.time.Time] = None
        self.observe_start_joints: Optional[List[float]] = None
        self.last_commanded_joints: Optional[List[float]] = None
        self.filtered_target_x: Optional[float] = None
        self.filtered_target_y: Optional[float] = None
        self.filtered_target_vx = 0.0
        self.filtered_target_vy = 0.0
        self.filtered_target_time: Optional[rclpy.time.Time] = None
        self.last_status_log_time = self.get_clock().now()
        self.last_debug_publish_time = self.get_clock().now()
        self.last_yaw_debug = ""
        self.last_pitch_debug = ""
        self.previous_error_time: Optional[rclpy.time.Time] = None
        self.previous_yaw_error = 0.0
        self.previous_pitch_error = 0.0
        self.filtered_yaw_error_rate = 0.0
        self.filtered_pitch_error_rate = 0.0
        self.previous_control_time: Optional[rclpy.time.Time] = None
        self.desired_yaw_velocity = 0.0
        self.yaw_velocity_integral = 0.0
        self.yaw_deadband_holding = True
        self.pitch_deadband_holding = True

        self.timer = self.create_timer(1.0 / self.command_rate_hz, self.control_tick)
        self.get_logger().info("Flame arm tracker ready. Enable with /flame_arm_tracker/set_enabled")

    def set_enabled_callback(self, request: SetBool.Request, response: SetBool.Response):
        if request.data:
            if self.latest_joint_state is None:
                response.success = False
                response.message = "No /joint_states feedback received yet."
                return response
            self.enabled = True
            self.mode = "observe"
            self.observe_start_time = self.get_clock().now()
            self.observe_start_joints = self._current_arm_joints()
            self.last_commanded_joints = list(self.observe_start_joints)
            self.latest_detection = None
            self.latest_detection_time = None
            self.consecutive_detection_count = 0
            self.last_yaw_debug = ""
            self.last_pitch_debug = ""
            self._reset_target_filter()
            self._reset_pd_state()
            response.success = True
            response.message = "Flame tracking enabled; moving to observe pose."
        else:
            self._publish_hold_current_pose()
            self.enabled = False
            self.mode = "idle"
            self.observe_start_time = None
            self.observe_start_joints = None
            self.last_commanded_joints = None
            self.latest_detection = None
            self.latest_detection_time = None
            self.consecutive_detection_count = 0
            self._reset_target_filter()
            self._reset_pd_state()
            response.success = True
            response.message = "Flame tracking disabled."
        return response

    def detections_callback(self, message: Detection2DArray) -> None:
        selected = self._select_detection(message.detections)
        if selected is None:
            self._clear_detection_state()
            return
        now = self.get_clock().now()
        if self._is_detection_jump(selected):
            self.consecutive_detection_count = 0
            self._reset_target_filter()
            self._reset_pd_state()
        self.consecutive_detection_count += 1
        if self.use_alpha_beta_filter:
            self._update_target_filter(selected.center_x, selected.center_y, now)
        elif self.latest_detection is not None and self.target_smoothing_alpha < 1.0:
            alpha = self.target_smoothing_alpha
            selected.center_x = (
                alpha * selected.center_x + (1.0 - alpha) * self.latest_detection.center_x
            )
            selected.center_y = (
                alpha * selected.center_y + (1.0 - alpha) * self.latest_detection.center_y
            )
            selected.size_x = (
                alpha * selected.size_x + (1.0 - alpha) * self.latest_detection.size_x
            )
            selected.size_y = (
                alpha * selected.size_y + (1.0 - alpha) * self.latest_detection.size_y
            )
        if self.consecutive_detection_count >= self.min_consecutive_detections:
            self.latest_detection = selected
            self.latest_detection_time = now

    def camera_info_callback(self, message: CameraInfo) -> None:
        if message.k[0] > 0.0 and message.k[4] > 0.0:
            self.latest_camera_info = message

    def joint_state_callback(self, message: JointState) -> None:
        self.latest_joint_state = {
            name: message.position[index]
            for index, name in enumerate(message.name)
            if index < len(message.position)
        }
        self.latest_joint_state_time = self.get_clock().now()
        self.latest_joint_velocity = {
            name: message.velocity[index]
            for index, name in enumerate(message.name)
            if index < len(message.velocity)
        }

    def cmd_vel_callback(self, message: Twist) -> None:
        self.latest_cmd_vel = message

    def control_tick(self) -> None:
        if not self.enabled or self.latest_joint_state is None:
            return

        if self.command_pub.get_subscription_count() == 0:
            self._reset_pd_state()
            self._throttled_status("No /joint_command subscriber; holding flame tracker output.")
            return

        if self._joint_state_is_stale():
            self._reset_pd_state()
            self._throttled_status("Joint state feedback timed out; holding flame tracker output.")
            return

        if self.mode == "observe":
            self._publish_observe_command()
            return

        if self.mode != "tracking":
            return

        if self.latest_camera_info is None:
            self._throttled_status("Waiting for camera_info before flame tracking.")
            return

        if self.latest_detection is None or self.latest_detection_time is None:
            self._throttled_status("Waiting for flame detection.")
            return

        target_age = (self.get_clock().now() - self.latest_detection_time).nanoseconds * 1e-9
        if target_age > self.tracking_timeout_sec:
            self._clear_detection_state()
            self._throttled_status("Flame detection timed out; pausing arm command.")
            return

        using_predicted_target = target_age > self.lost_target_prediction_start_sec
        if using_predicted_target:
            if self.lost_target_prediction_speed_scale <= 0.0:
                self._reset_pd_state()
                self._throttled_status("Flame detection stale; pausing arm command.")
                return
            self._throttled_status("Flame detection stale; predicting target center.")

        command = self._build_tracking_command(target_age, using_predicted_target)
        self._publish_joint_command(command)

    def _publish_observe_command(self) -> None:
        if self.observe_start_time is None or self.observe_start_joints is None:
            self.mode = "tracking"
            return

        elapsed = (self.get_clock().now() - self.observe_start_time).nanoseconds * 1e-9
        alpha = max(0.0, min(1.0, elapsed / self.observe_duration_sec))
        alpha = alpha * alpha * (3.0 - 2.0 * alpha)
        if elapsed >= self.observe_duration_sec:
            command = list(self.observe_joints)
        else:
            command = [
                self.observe_start_joints[index] +
                (self.observe_joints[index] - self.observe_start_joints[index]) * alpha
                for index in range(6)
            ]
        self._publish_joint_command(command)

        observe_error = self._max_abs_joint_error(self.observe_joints)
        if observe_error <= self.observe_position_tolerance_rad:
            self.mode = "tracking"
            self._reset_pd_state()
            self.previous_control_time = None
            self.desired_yaw_velocity = 0.0
            self.yaw_velocity_integral = 0.0
            self.get_logger().info("Observe pose reached; entering flame tracking mode.")
        elif elapsed >= self.observe_duration_sec:
            self._throttled_status(
                "Moving to observe pose; max joint error %.3f rad." % observe_error
            )

    def _build_tracking_command(
        self,
        target_age: float = 0.0,
        using_predicted_target: bool = False,
    ) -> List[float]:
        feedback = self._current_arm_joints()
        if not self.use_command_accumulator or self.last_commanded_joints is None:
            current = feedback
        else:
            current = list(self.last_commanded_joints)
            current[0] = self._limit_command_lead(current[0], feedback[0])
            current[4] = self._limit_command_lead(current[4], feedback[4])
            current[5] = self._limit_command_lead(current[5], feedback[5])
        camera = self.latest_camera_info
        detection = self.latest_detection
        assert camera is not None
        assert detection is not None

        dt = self._control_dt()
        target_x, target_y = self._predicted_target_center(camera)
        desired_center_x = camera.k[2] + self.target_center_offset_x_px
        desired_center_y = camera.k[5] + self.target_center_offset_y_px

        yaw_error = math.atan2(target_x - desired_center_x, camera.k[0])
        pitch_error = math.atan2(target_y - desired_center_y, camera.k[4])
        yaw_error = self._apply_deadband_hysteresis(yaw_error, "yaw")
        pitch_error = self._apply_deadband_hysteresis(pitch_error, "pitch")

        yaw_error_rate, pitch_error_rate = self._filtered_error_rates(yaw_error, pitch_error)

        yaw_p = self.outer_kp_yaw * yaw_error
        yaw_d = self.outer_kd_yaw * yaw_error_rate
        yaw_ff = self.cmd_vel_yaw_feedforward_gain * self.latest_cmd_vel.angular.z
        if yaw_error == 0.0 and abs(yaw_ff) < 1e-6:
            self.desired_yaw_velocity = 0.0
            self.yaw_velocity_integral = 0.0
            yaw_delta = 0.0
        else:
            yaw_delta = self._servo_yaw_delta(
                yaw_p,
                yaw_d,
                yaw_ff,
                dt,
                self._target_speed_scale(using_predicted_target),
            )
        pitch_p = self.kp_pitch * pitch_error
        pitch_d = self.kd_pitch * pitch_error_rate
        pitch_delta = pitch_p + pitch_d

        command = list(current)
        command[0] = self._apply_delta_limit(command[0], yaw_delta, 0)
        command[4] = self._apply_delta_limit(
            command[4],
            self.pitch_joint5_sign * pitch_delta,
            4,
        )
        command[5] = self._apply_delta_limit(
            command[5],
            self.pitch_joint6_sign * pitch_delta,
            5,
        )
        self.last_yaw_debug = (
            "age=%.3f predicted=%s cx=%.1f raw_x=%.1f target_x=%.1f "
            "yaw_error=%.4f yaw_p=%.4f yaw_d=%.4f "
            "yaw_rate=%.4f yaw_ff=%.4f desired_vel=%.4f measured_vel=%.4f "
            "vel_i=%.4f delta=%.4f base1=%.4f feedback1=%.4f cmd1=%.4f"
            % (
                target_age,
                str(using_predicted_target),
                camera.k[2],
                detection.center_x,
                target_x,
                yaw_error,
                yaw_p,
                yaw_d,
                yaw_error_rate,
                yaw_ff,
                self.desired_yaw_velocity,
                self._joint_velocity(0),
                self.yaw_velocity_integral,
                command[0] - current[0],
                current[0],
                feedback[0],
                command[0],
            )
        )
        self.last_pitch_debug = (
            "cy=%.1f target_y=%.1f pitch_error=%.4f pitch_p=%.4f pitch_d=%.4f pitch_rate=%.4f "
            "joint5=%.4f cmd5=%.4f joint6=%.4f cmd6=%.4f"
            % (
                camera.k[5],
                target_y,
                pitch_error,
                pitch_p,
                pitch_d,
                pitch_error_rate,
                current[4],
                command[4],
                current[5],
                command[5],
            )
        )
        self._publish_debug()
        return command

    def _apply_deadband_hysteresis(self, error: float, axis: str) -> float:
        deadband = self.deadband_rad
        if deadband <= 0.0:
            if axis == "yaw":
                self.yaw_deadband_holding = False
            else:
                self.pitch_deadband_holding = False
            return error

        release_deadband = deadband + self.deadband_hysteresis_rad
        holding = self.yaw_deadband_holding if axis == "yaw" else self.pitch_deadband_holding
        abs_error = abs(error)
        if holding:
            should_hold = abs_error <= release_deadband
        else:
            should_hold = abs_error <= deadband

        if axis == "yaw":
            self.yaw_deadband_holding = should_hold
        else:
            self.pitch_deadband_holding = should_hold
        return 0.0 if should_hold else error

    def _control_dt(self) -> float:
        now = self.get_clock().now()
        if self.previous_control_time is None:
            self.previous_control_time = now
            return 1.0 / self.command_rate_hz

        dt = (now - self.previous_control_time).nanoseconds * 1e-9
        self.previous_control_time = now
        if dt <= 1e-4:
            return 1.0 / self.command_rate_hz
        return min(0.20, dt)

    def _predicted_target_center(self, camera: CameraInfo) -> tuple[float, float]:
        detection = self.latest_detection
        assert detection is not None

        if (
            not self.use_alpha_beta_filter
            or self.filtered_target_x is None
            or self.filtered_target_y is None
        ):
            return detection.center_x, detection.center_y

        lead = self.target_prediction_sec
        if self.filtered_target_time is not None:
            lead += max(
                0.0,
                (self.get_clock().now() - self.filtered_target_time).nanoseconds * 1e-9,
            )

        target_x = self.filtered_target_x + self.filtered_target_vx * lead
        target_y = self.filtered_target_y + self.filtered_target_vy * lead
        width = float(camera.width) if camera.width else 2.0 * camera.k[2]
        height = float(camera.height) if camera.height else 2.0 * camera.k[5]
        return self._clip(target_x, 0.0, width - 1.0), self._clip(target_y, 0.0, height - 1.0)

    def _dual_loop_yaw_delta(
        self,
        yaw_p: float,
        yaw_d: float,
        yaw_ff: float,
        dt: float,
        speed_scale: float = 1.0,
    ) -> float:
        max_yaw_velocity = self.max_yaw_velocity_rad_s * speed_scale
        max_yaw_accel = self.max_yaw_accel_rad_s2 * speed_scale
        raw_desired_velocity = self.yaw_joint_sign * (yaw_p + yaw_d) + yaw_ff
        desired_velocity = self._clip(
            raw_desired_velocity,
            -max_yaw_velocity,
            max_yaw_velocity,
        )
        if max_yaw_accel > 0.0:
            max_velocity_step = max_yaw_accel * dt
            desired_velocity = self._clip(
                desired_velocity,
                self.desired_yaw_velocity - max_velocity_step,
                self.desired_yaw_velocity + max_velocity_step,
            )
        self.desired_yaw_velocity = desired_velocity

        measured_velocity = self._joint_velocity(0)
        velocity_error = desired_velocity - measured_velocity
        self.yaw_velocity_integral += velocity_error * dt
        if self.max_yaw_velocity_integral > 0.0:
            self.yaw_velocity_integral = self._clip(
                self.yaw_velocity_integral,
                -self.max_yaw_velocity_integral,
                self.max_yaw_velocity_integral,
            )
        else:
            self.yaw_velocity_integral = 0.0

        corrected_velocity = (
            desired_velocity
            + self.inner_kp_yaw_velocity * velocity_error
            + self.inner_ki_yaw_velocity * self.yaw_velocity_integral
        )
        corrected_velocity = self._clip(
            corrected_velocity,
            -max_yaw_velocity,
            max_yaw_velocity,
        )
        return corrected_velocity * dt

    def _servo_yaw_delta(
        self,
        yaw_p: float,
        yaw_d: float,
        yaw_ff: float,
        dt: float,
        speed_scale: float = 1.0,
    ) -> float:
        max_yaw_velocity = self.max_yaw_velocity_rad_s * speed_scale
        max_yaw_accel = self.max_yaw_accel_rad_s2 * speed_scale
        desired_velocity = self.yaw_joint_sign * (yaw_p + yaw_d) + yaw_ff
        desired_velocity = self._clip(
            desired_velocity,
            -max_yaw_velocity,
            max_yaw_velocity,
        )
        if max_yaw_accel > 0.0:
            max_velocity_step = max_yaw_accel * dt
            desired_velocity = self._clip(
                desired_velocity,
                self.desired_yaw_velocity - max_velocity_step,
                self.desired_yaw_velocity + max_velocity_step,
            )
        self.desired_yaw_velocity = desired_velocity
        return desired_velocity * dt

    def _target_speed_scale(self, using_predicted_target: bool) -> float:
        if not using_predicted_target:
            return 1.0
        return self.lost_target_prediction_speed_scale

    def _joint_velocity(self, joint_index: int) -> float:
        state = self.latest_joint_velocity or {}
        return float(state.get(f"joint{joint_index + 1}", 0.0))

    def _joint_state_is_stale(self) -> bool:
        if self.latest_joint_state_time is None:
            return True
        age = (self.get_clock().now() - self.latest_joint_state_time).nanoseconds * 1e-9
        return age > self.joint_state_timeout_sec

    def _apply_delta_limit(self, current_value: float, desired_delta: float, joint_index: int) -> float:
        limit = abs(self.joint_delta_limits[joint_index])
        if limit <= 0.0:
            delta = 0.0
        else:
            delta = max(-limit, min(limit, desired_delta))

        candidate = current_value + delta
        lower = self.joint_min_limits[joint_index]
        upper = self.joint_max_limits[joint_index]
        if candidate < lower:
            return lower
        if candidate > upper:
            return upper
        return candidate

    def _filtered_error_rates(self, yaw_error: float, pitch_error: float) -> tuple[float, float]:
        now = self.get_clock().now()
        if self.previous_error_time is None:
            self.previous_error_time = now
            self.previous_yaw_error = yaw_error
            self.previous_pitch_error = pitch_error
            self.filtered_yaw_error_rate = 0.0
            self.filtered_pitch_error_rate = 0.0
            return 0.0, 0.0

        dt = (now - self.previous_error_time).nanoseconds * 1e-9
        self.previous_error_time = now
        if dt <= 1e-4:
            return self.filtered_yaw_error_rate, self.filtered_pitch_error_rate

        raw_yaw_rate = (yaw_error - self.previous_yaw_error) / dt
        raw_pitch_rate = (pitch_error - self.previous_pitch_error) / dt
        alpha = self.derivative_filter_alpha
        self.filtered_yaw_error_rate = (
            alpha * raw_yaw_rate + (1.0 - alpha) * self.filtered_yaw_error_rate
        )
        self.filtered_pitch_error_rate = (
            alpha * raw_pitch_rate + (1.0 - alpha) * self.filtered_pitch_error_rate
        )
        self.previous_yaw_error = yaw_error
        self.previous_pitch_error = pitch_error
        return self.filtered_yaw_error_rate, self.filtered_pitch_error_rate

    def _limit_command_lead(self, commanded_value: float, feedback_value: float) -> float:
        lead = self.max_command_feedback_lead
        if lead <= 0.0:
            return commanded_value
        return max(feedback_value - lead, min(feedback_value + lead, commanded_value))

    def _update_target_filter(
        self,
        measured_x: float,
        measured_y: float,
        stamp: rclpy.time.Time,
    ) -> None:
        if (
            self.filtered_target_x is None
            or self.filtered_target_y is None
            or self.filtered_target_time is None
        ):
            self.filtered_target_x = measured_x
            self.filtered_target_y = measured_y
            self.filtered_target_vx = 0.0
            self.filtered_target_vy = 0.0
            self.filtered_target_time = stamp
            return

        dt = (stamp - self.filtered_target_time).nanoseconds * 1e-9
        self.filtered_target_time = stamp
        if dt <= 1e-4:
            return

        predicted_x = self.filtered_target_x + self.filtered_target_vx * dt
        predicted_y = self.filtered_target_y + self.filtered_target_vy * dt
        residual_x = measured_x - predicted_x
        residual_y = measured_y - predicted_y

        self.filtered_target_x = predicted_x + self.alpha_beta_alpha * residual_x
        self.filtered_target_y = predicted_y + self.alpha_beta_alpha * residual_y
        self.filtered_target_vx += self.alpha_beta_beta * residual_x / dt
        self.filtered_target_vy += self.alpha_beta_beta * residual_y / dt

    def _reset_target_filter(self) -> None:
        self.filtered_target_x = None
        self.filtered_target_y = None
        self.filtered_target_vx = 0.0
        self.filtered_target_vy = 0.0
        self.filtered_target_time = None

    def _reset_pd_state(self) -> None:
        self.previous_error_time = None
        self.previous_yaw_error = 0.0
        self.previous_pitch_error = 0.0
        self.filtered_yaw_error_rate = 0.0
        self.filtered_pitch_error_rate = 0.0
        self.previous_control_time = None
        self.desired_yaw_velocity = 0.0
        self.yaw_velocity_integral = 0.0
        self.yaw_deadband_holding = True
        self.pitch_deadband_holding = True

    def _clear_detection_state(self) -> None:
        self.latest_detection = None
        self.latest_detection_time = None
        self.consecutive_detection_count = 0
        self._reset_target_filter()
        self._reset_pd_state()

    def _is_detection_jump(self, selected: Detection2D) -> bool:
        if self.latest_detection is None or self.max_detection_jump_px <= 0.0:
            return False
        dx = selected.center_x - self.latest_detection.center_x
        dy = selected.center_y - self.latest_detection.center_y
        return math.hypot(dx, dy) > self.max_detection_jump_px

    def _clip(self, value: float, lower: float, upper: float) -> float:
        return max(lower, min(upper, value))

    def _publish_joint_command(self, positions: List[float]) -> None:
        self.last_commanded_joints = [float(value) for value in positions]
        message = JointState()
        message.header.stamp = self.get_clock().now().to_msg()
        message.header.frame_id = "piper_single"
        message.name = [f"joint{index}" for index in range(1, 7)]
        message.position = [float(value) for value in positions]
        message.velocity = [self.command_velocity] * 6
        message.effort = [0.0] * 6
        self.command_pub.publish(message)

    def _publish_hold_current_pose(self) -> None:
        if self.latest_joint_state is None or self.command_pub.get_subscription_count() == 0:
            return
        self._publish_joint_command(self._current_arm_joints())

    def _select_detection(self, detections: List[Detection2D]) -> Optional[Detection2D]:
        candidates = [
            detection for detection in detections
            if not self.target_class_name or detection.class_name == self.target_class_name
        ]
        if not candidates:
            return None
        return max(candidates, key=lambda detection: detection.confidence)

    def _current_arm_joints(self) -> List[float]:
        state = self.latest_joint_state or {}
        return [float(state.get(f"joint{index}", 0.0)) for index in range(1, 7)]

    def _max_abs_joint_error(self, target: List[float]) -> float:
        current = self._current_arm_joints()
        return max(abs(target[index] - current[index]) for index in range(6))

    def _read_six_float_parameter(self, name: str) -> List[float]:
        values = [float(value) for value in self.get_parameter(name).value]
        if len(values) != 6:
            raise ValueError("Parameter '%s' must contain exactly 6 values." % name)
        return values

    def _throttled_status(self, message: str) -> None:
        now = self.get_clock().now()
        if (now - self.last_status_log_time).nanoseconds * 1e-9 > 1.0:
            self.get_logger().info(message)
            self.last_status_log_time = now

    def _publish_debug(self) -> None:
        now = self.get_clock().now()
        if (now - self.last_debug_publish_time).nanoseconds * 1e-9 < 0.20:
            return
        message = String()
        message.data = self.last_yaw_debug + " | " + self.last_pitch_debug
        self.debug_pub.publish(message)
        self.last_debug_publish_time = now


def main() -> None:
    rclpy.init()
    node: Optional[FlameArmTracker] = None
    try:
        node = FlameArmTracker()
        rclpy.spin(node)
    finally:
        if node is not None:
            node.destroy_node()
        rclpy.shutdown()
