import time
from collections import deque
from threading import Lock

import rclpy
from printed_number_interfaces.srv import ReadPrintedNumber
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node


class PrintedNumberReader(Node):
    def __init__(self):
        super().__init__('printed_number_reader')
        self.declare_parameter('service_name', '/perception/read_printed_number')
        self.declare_parameter('detections_topic', '/perception/digit_detections')
        self.declare_parameter('reader_mode', 'mock')
        self.declare_parameter('mock_value', '12345')
        self.declare_parameter('mock_confidence', 1.0)
        self.declare_parameter('default_timeout_sec', 3.0)
        self.declare_parameter('min_confidence', 0.7)
        self.declare_parameter('expected_digits', 0)
        self.declare_parameter('stable_frames', 1)
        self.declare_parameter('max_detection_age_sec', 1.0)
        self.declare_parameter('poll_interval_sec', 0.05)

        self._cb_group = ReentrantCallbackGroup()
        self._frames = deque(maxlen=max(1, int(self.get_parameter('stable_frames').value) * 5))
        self._frames_lock = Lock()
        self._yolo_available = False

        try:
            from yolo_interfaces.msg import YoloDetections
        except ImportError as exc:
            self.get_logger().warning(
                f'yolo_interfaces unavailable; yolo reader_mode will fail: {exc}'
            )
        else:
            self._yolo_available = True
            self.create_subscription(
                YoloDetections,
                str(self.get_parameter('detections_topic').value),
                self._on_detections,
                10,
                callback_group=self._cb_group,
            )
        self.create_service(
            ReadPrintedNumber,
            str(self.get_parameter('service_name').value),
            self._handle_read,
            callback_group=self._cb_group,
        )

    def _on_detections(self, msg):
        with self._frames_lock:
            self._frames.append((time.monotonic(), msg))

    def _handle_read(self, request, response):
        try:
            mode = str(self.get_parameter('reader_mode').value).strip().lower()
            if mode == 'mock':
                return self._handle_mock(request, response)
            if mode == 'yolo':
                return self._handle_yolo(request, response)
            return self._fail(response, f'invalid reader_mode: {mode}')
        except Exception as exc:  # keep service robust
            self.get_logger().warning(f'read request failed: {exc}')
            return self._fail(response, f'read failed: {exc}')

    def _handle_mock(self, request, response):
        value = str(self.get_parameter('mock_value').value)
        confidence = float(self.get_parameter('mock_confidence').value)
        return self._validate_and_fill(request, response, value, confidence, 'mock read ok')

    def _handle_yolo(self, request, response):
        if not self._yolo_available:
            return self._fail(response, 'yolo_interfaces unavailable; cannot use yolo reader_mode')

        timeout = float(request.timeout_sec) if request.timeout_sec > 0.0 else float(
            self.get_parameter('default_timeout_sec').value
        )
        deadline = time.monotonic() + max(timeout, 0.0)
        poll = max(float(self.get_parameter('poll_interval_sec').value), 0.01)

        last_error = 'no detection frame received'
        while time.monotonic() <= deadline and rclpy.ok():
            result = self._stable_result(request)
            if result[0]:
                value, confidence = result[1], result[2]
                return self._validate_and_fill(request, response, value, confidence, 'yolo read ok')
            last_error = result[3]
            time.sleep(poll)
        return self._fail(response, f'timeout waiting for printed number: {last_error}')

    def _stable_result(self, request):
        min_conf = self._request_min_confidence(request)
        expected = self._request_expected_digits(request)
        stable_frames = max(int(self.get_parameter('stable_frames').value), 1)
        max_age = max(float(self.get_parameter('max_detection_age_sec').value), 0.0)
        now = time.monotonic()
        with self._frames_lock:
            frames = list(self._frames)

        parsed = []
        for stamp, msg in reversed(frames):
            if max_age > 0.0 and now - stamp > max_age:
                continue
            value, confidence, error = self._parse_frame(msg, min_conf, expected)
            if value:
                parsed.append((value, confidence))
            elif not parsed:
                last_error = error
        if not parsed:
            return False, '', 0.0, locals().get('last_error', 'no fresh valid digit detections')

        value = parsed[0][0]
        matches = [conf for val, conf in parsed if val == value]
        if len(matches) < stable_frames:
            return False, '', 0.0, f'value not stable for {stable_frames} frame(s)'
        return True, value, sum(matches[:stable_frames]) / stable_frames, 'ok'

    def _parse_frame(self, msg, min_confidence, expected_digits):
        digits = []
        for det in msg.detections:
            score = float(det.hypothesis.score)
            name = str(det.hypothesis.class_name)
            if score < min_confidence or len(name) != 1 or not name.isdigit():
                continue
            digits.append((float(det.bbox.center_x), name, score))
        if not digits:
            return '', 0.0, 'no digit detections above confidence threshold'
        digits.sort(key=lambda item: item[0])
        value = ''.join(item[1] for item in digits)
        if expected_digits > 0 and len(value) != expected_digits:
            return '', 0.0, f'expected {expected_digits} digits, got {len(value)}'
        confidence = sum(item[2] for item in digits) / len(digits)
        return value, confidence, 'ok'

    def _validate_and_fill(self, request, response, value, confidence, message):
        expected = self._request_expected_digits(request)
        min_conf = self._request_min_confidence(request)
        if not value.isdigit():
            return self._fail(response, f'value is not pure digits: {value}')
        if expected > 0 and len(value) != expected:
            return self._fail(response, f'expected {expected} digits, got {len(value)}')
        if confidence < min_conf:
            return self._fail(response, f'confidence {confidence:.3f} below {min_conf:.3f}')
        response.success = True
        response.value = value
        response.confidence = float(confidence)
        response.message = message
        return response

    def _request_expected_digits(self, request):
        return int(request.expected_digits) if request.expected_digits > 0 else int(
            self.get_parameter('expected_digits').value
        )

    def _request_min_confidence(self, request):
        return float(request.min_confidence) if request.min_confidence > 0.0 else float(
            self.get_parameter('min_confidence').value
        )

    @staticmethod
    def _fail(response, message):
        response.success = False
        response.value = ''
        response.confidence = 0.0
        response.message = message
        return response


def main(args=None):
    rclpy.init(args=args)
    node = PrintedNumberReader()
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    try:
        executor.spin()
    finally:
        executor.shutdown()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
