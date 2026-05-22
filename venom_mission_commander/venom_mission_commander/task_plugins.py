import time
from typing import Any

import rclpy

from venom_mission_commander.models import TaskContext, TaskExecutionResult, TaskSpec


class BaseTaskPlugin:
    task_type = 'base'

    def configure(self, node: Any) -> None:
        self.node = node

    def execute(self, context: TaskContext, spec: TaskSpec) -> TaskExecutionResult:
        raise NotImplementedError

    def cancel(self) -> None:
        return None

    def _sleep(self, seconds: float) -> None:
        time.sleep(max(float(seconds), 0.0))


class DetectItemTaskPlugin(BaseTaskPlugin):
    task_type = 'detect_item'

    def execute(self, context: TaskContext, spec: TaskSpec) -> TaskExecutionResult:
        target = str(spec.params.get('target', 'unknown_item'))
        delay_sec = float(spec.params.get('mock_delay_sec', 0.5))
        self.node.get_logger().info(f'[MOCK TASK] Detecting item: {target}')
        self._sleep(delay_sec)

        detection = {
            'target': target,
            'confidence': float(spec.params.get('mock_confidence', 0.92)),
            'pose_frame': str(spec.params.get('mock_pose_frame', 'camera_link')),
            'pose_hint': spec.params.get('mock_pose_hint', 'mock_center'),
        }
        context.blackboard['detected_item'] = detection
        return TaskExecutionResult(True, f'detected item: {target}', detection)


class GraspItemTaskPlugin(BaseTaskPlugin):
    task_type = 'grasp_item'

    def execute(self, context: TaskContext, spec: TaskSpec) -> TaskExecutionResult:
        source_key = str(spec.params.get('source', 'detected_item'))
        target = context.blackboard.get(source_key)
        if target is None:
            return TaskExecutionResult(False, f'missing grasp target: {source_key}')

        delay_sec = float(spec.params.get('mock_delay_sec', 1.0))
        self.node.get_logger().info(f'[MOCK TASK] Grasping item from {source_key}: {target}')
        self._sleep(delay_sec)

        grasped_object = {
            'source': source_key,
            'object': target,
            'gripper': str(spec.params.get('gripper', 'piper')),
        }
        context.blackboard['grasped_object'] = grasped_object
        context.blackboard['last_grasp_success'] = True
        return TaskExecutionResult(True, 'grasp succeeded', grasped_object)


class ReadMeterTaskPlugin(BaseTaskPlugin):
    task_type = 'read_meter'

    def execute(self, context: TaskContext, spec: TaskSpec) -> TaskExecutionResult:
        backend = str(spec.params.get('backend', 'mock')).strip().lower()
        if backend == 'service':
            return self._execute_service(context, spec)
        if backend not in ('mock', ''):
            return TaskExecutionResult(False, f'unknown read_meter backend: {backend}')

        meter_id = str(spec.params.get('meter_id', 'meter_1'))
        delay_sec = float(spec.params.get('mock_delay_sec', 0.5))
        value = spec.params.get('mock_value', '220.0V')
        self.node.get_logger().info(f'[MOCK TASK] Reading meter image: {meter_id}')
        self._sleep(delay_sec)

        reading = {
            'meter_id': meter_id,
            'value': value,
            'confidence': float(spec.params.get('mock_confidence', 0.9)),
        }
        context.blackboard['meter_reading'] = reading
        return TaskExecutionResult(True, f'meter {meter_id}={value}', reading)

    def _execute_service(self, context: TaskContext, spec: TaskSpec) -> TaskExecutionResult:
        try:
            from printed_number_interfaces.srv import ReadPrintedNumber
        except Exception as exc:
            return TaskExecutionResult(False, f'ReadPrintedNumber import failed: {exc}')

        meter_id = str(spec.params.get('meter_id', 'meter_1'))
        service_name = str(spec.params.get('service_name', '/perception/read_printed_number'))
        timeout_sec = float(spec.params.get('timeout_sec', 5.0))
        if timeout_sec <= 0.0:
            return TaskExecutionResult(False, 'timeout_sec must be positive for service backend')
        output_key = str(spec.params.get('output_key', 'meter_reading'))
        expected_digits = int(spec.params.get('expected_digits', 0))
        min_confidence = float(spec.params.get('min_confidence', 0.0))
        service_wait_timeout_sec = min(
            float(spec.params.get('service_wait_timeout_sec', 1.0)),
            timeout_sec,
        )

        client = self.node.create_client(ReadPrintedNumber, service_name)
        try:
            start_time = time.monotonic()
            if not client.wait_for_service(timeout_sec=max(service_wait_timeout_sec, 0.0)):
                return TaskExecutionResult(False, f'service unavailable: {service_name}')
            remaining_timeout_sec = timeout_sec - (time.monotonic() - start_time)
            if remaining_timeout_sec <= 0.0:
                return TaskExecutionResult(False, f'service wait timeout: {service_name}')

            request = ReadPrintedNumber.Request()
            request.target_id = meter_id
            request.timeout_sec = float(remaining_timeout_sec)
            request.expected_digits = max(expected_digits, 0)
            request.min_confidence = max(min_confidence, 0.0)

            future = client.call_async(request)
            deadline = time.monotonic() + max(remaining_timeout_sec, 0.0) + 0.2
            while rclpy.ok() and not future.done() and time.monotonic() < deadline:
                rclpy.spin_once(self.node, timeout_sec=0.05)

            if not future.done():
                return TaskExecutionResult(False, f'read meter service timeout: {service_name}')

            response = future.result()
            if response is None:
                return TaskExecutionResult(False, 'read meter service returned no response')
            if not response.success:
                return TaskExecutionResult(False, f'read meter failed: {response.message}')

            value = str(response.value)
            confidence = float(response.confidence)
            if not value.isdigit():
                return TaskExecutionResult(False, f'read value is not pure digits: {value}')
            if expected_digits > 0 and len(value) != expected_digits:
                return TaskExecutionResult(
                    False,
                    f'expected {expected_digits} digits, got {len(value)}',
                )
            if confidence < min_confidence:
                return TaskExecutionResult(
                    False,
                    f'confidence {confidence:.3f} below {min_confidence:.3f}',
                )

            reading = {
                'meter_id': meter_id,
                'value': value,
                'confidence': confidence,
                'source': 'printed_number_service',
            }
            context.blackboard[output_key] = reading
            return TaskExecutionResult(True, f'meter {meter_id}={value}', reading)
        except Exception as exc:
            return TaskExecutionResult(False, f'read meter service error: {exc}')
        finally:
            self.node.destroy_client(client)


class VoiceReportTaskPlugin(BaseTaskPlugin):
    task_type = 'voice_report'

    def execute(self, context: TaskContext, spec: TaskSpec) -> TaskExecutionResult:
        reading = context.blackboard.get('meter_reading', {})
        default_text = (
            f"电表 {reading.get('meter_id', 'unknown')} 读数 "
            f"{reading.get('value', 'unknown')}，执行播报操作"
        )
        text = str(spec.params.get('text', default_text))
        delay_sec = float(spec.params.get('mock_delay_sec', 0.2))
        self.node.get_logger().info(f'[MOCK TASK] Voice report: {text}')
        self._sleep(delay_sec)

        report = {'text': text, 'source': 'mock_tts'}
        context.blackboard['last_voice_report'] = report
        return TaskExecutionResult(True, 'voice report completed', report)


class DetectFlameTaskPlugin(BaseTaskPlugin):
    task_type = 'detect_flame'

    def execute(self, context: TaskContext, spec: TaskSpec) -> TaskExecutionResult:
        delay_sec = float(spec.params.get('mock_delay_sec', 0.5))
        self.node.get_logger().info('[MOCK TASK] Detecting flame image.')
        self._sleep(delay_sec)

        detection = {
            'class': 'flame',
            'confidence': float(spec.params.get('mock_confidence', 0.88)),
            'bbox': spec.params.get('mock_bbox', [320, 180, 80, 120]),
        }
        context.blackboard['flame_detection'] = detection
        return TaskExecutionResult(True, 'flame detected', detection)


class TrackFlameTaskPlugin(BaseTaskPlugin):
    task_type = 'track_flame'

    def execute(self, context: TaskContext, spec: TaskSpec) -> TaskExecutionResult:
        source_key = str(spec.params.get('source', 'flame_detection'))
        flame = context.blackboard.get(source_key)
        if flame is None:
            return TaskExecutionResult(False, f'missing flame detection: {source_key}')

        steps = int(spec.params.get('mock_tracking_steps', 3))
        step_delay_sec = float(spec.params.get('mock_step_delay_sec', 0.2))
        for index in range(max(steps, 1)):
            self.node.get_logger().info(f'[MOCK TASK] Tracking flame step {index + 1}/{steps}')
            self._sleep(step_delay_sec)

        tracking = {'source': source_key, 'status': 'tracked', 'steps': steps}
        context.blackboard['last_flame_tracking'] = tracking
        return TaskExecutionResult(True, 'flame tracking completed', tracking)


class ClassifyPlaceTaskPlugin(BaseTaskPlugin):
    task_type = 'classify_place'

    def execute(self, context: TaskContext, spec: TaskSpec) -> TaskExecutionResult:
        source_key = str(spec.params.get('source', 'grasped_object'))
        grasped_object = context.blackboard.get(source_key)
        if grasped_object is None:
            return TaskExecutionResult(False, f'missing object to place: {source_key}')

        category = str(spec.params.get('mock_category', 'default_category'))
        place_zone = str(spec.params.get('place_zone', 'default_bin'))
        delay_sec = float(spec.params.get('mock_delay_sec', 1.0))
        self.node.get_logger().info(
            f'[MOCK TASK] Classifying object as {category}, placing to {place_zone}'
        )
        self._sleep(delay_sec)

        placement = {
            'source': source_key,
            'category': category,
            'place_zone': place_zone,
            'object': grasped_object,
        }
        context.blackboard['last_placement'] = placement
        return TaskExecutionResult(True, 'classify and place completed', placement)


class WaitTaskPlugin(BaseTaskPlugin):
    task_type = 'wait'

    def execute(self, context: TaskContext, spec: TaskSpec) -> TaskExecutionResult:
        seconds = float(spec.params.get('seconds', 1.0))
        self.node.get_logger().info(f'[MOCK TASK] Waiting for {seconds:.2f}s')
        self._sleep(seconds)
        return TaskExecutionResult(True, f'waited {seconds:.2f}s')


class TaskPluginRegistry:
    def __init__(self):
        self.plugins: dict[str, BaseTaskPlugin] = {}

    def register(self, plugin: BaseTaskPlugin) -> None:
        self.plugins[plugin.task_type] = plugin

    def get(self, task_type: str) -> BaseTaskPlugin:
        if task_type not in self.plugins:
            available = ', '.join(sorted(self.plugins))
            raise RuntimeError(f'Unknown task type: {task_type}; available: {available}')
        return self.plugins[task_type]

    def has(self, task_type: str) -> bool:
        return task_type in self.plugins

    def available_types(self) -> list[str]:
        return sorted(self.plugins)

    def register_default_plugins(self, node: Any) -> None:
        for plugin in [
            DetectItemTaskPlugin(),
            GraspItemTaskPlugin(),
            ReadMeterTaskPlugin(),
            VoiceReportTaskPlugin(),
            DetectFlameTaskPlugin(),
            TrackFlameTaskPlugin(),
            ClassifyPlaceTaskPlugin(),
            WaitTaskPlugin(),
        ]:
            plugin.configure(node)
            self.register(plugin)
