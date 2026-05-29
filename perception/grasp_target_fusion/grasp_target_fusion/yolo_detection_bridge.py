import rclpy
from rclpy.node import Node
from venom_manipulation_interfaces.msg import Detection2D, Detection2DArray
from yolo_interfaces.msg import YoloDetection, YoloDetections


class YoloDetectionBridge(Node):
    def __init__(self) -> None:
        super().__init__("yolo_detection_bridge")
        self.debug_counter = 0

        self.declare_parameter("input_topic", "/perception/detections")
        self.declare_parameter("output_topic", "/perception/detections_2d")
        self.declare_parameter("output_array_topic", "/perception/detections_2d_array")
        self.declare_parameter("default_frame_id", "d435i_color_optical_frame")
        self.declare_parameter("allowed_classes", "")
        self.declare_parameter("min_confidence", 0.0)

        input_topic = str(self.get_parameter("input_topic").value)
        output_topic = str(self.get_parameter("output_topic").value)
        output_array_topic = str(self.get_parameter("output_array_topic").value)
        self.default_frame_id = str(self.get_parameter("default_frame_id").value)
        allowed_classes = str(self.get_parameter("allowed_classes").value)
        self.allowed_classes = {
            name.strip().lower() for name in allowed_classes.split(",") if name.strip()
        }
        self.min_confidence = float(self.get_parameter("min_confidence").value)

        self.single_publisher = self.create_publisher(Detection2D, output_topic, 10)
        self.array_publisher = self.create_publisher(Detection2DArray, output_array_topic, 10)

        self.create_subscription(
            YoloDetections,
            input_topic,
            self.detections_callback,
            10,
        )

        self.get_logger().info(
            "YOLO detection bridge ready. "
            f"input={input_topic}, output={output_topic}, output_array={output_array_topic}"
        )

    def detections_callback(self, message: YoloDetections) -> None:
        self.debug_counter += 1
        if self.debug_counter <= 5 or self.debug_counter % 20 == 0:
            preview = [
                f"{det.hypothesis.class_name}:{float(det.hypothesis.score):.3f}"
                for det in message.detections[:5]
            ]
            self.get_logger().info(
                "YOLO bridge debug: received %d detections raw=%s"
                % (len(message.detections), preview)
            )

        converted = [
            self._convert_detection(message, detection)
            for detection in message.detections
            if self._should_keep_detection(detection)
        ]

        if self.debug_counter <= 5 or self.debug_counter % 20 == 0:
            preview = [
                f"{det.class_name}:{float(det.confidence):.3f}"
                for det in converted[:5]
            ]
            self.get_logger().info(
                "YOLO bridge debug: kept %d detections filtered=%s"
                % (len(converted), preview)
            )

        array_message = Detection2DArray()
        array_message.header = message.header
        if not array_message.header.frame_id:
            array_message.header.frame_id = self.default_frame_id
        array_message.detections = converted
        self.array_publisher.publish(array_message)

        if converted:
            self.single_publisher.publish(converted[0])

    def _should_keep_detection(self, detection: YoloDetection) -> bool:
        if float(detection.hypothesis.score) < self.min_confidence:
            return False
        if not self.allowed_classes:
            return True
        return detection.hypothesis.class_name.strip().lower() in self.allowed_classes

    def _convert_detection(
        self,
        source_message: YoloDetections,
        detection: YoloDetection,
    ) -> Detection2D:
        converted = Detection2D()
        converted.header = source_message.header
        if not converted.header.frame_id:
            converted.header.frame_id = self.default_frame_id
        converted.class_name = detection.hypothesis.class_name
        converted.confidence = float(detection.hypothesis.score)
        converted.center_x = float(detection.bbox.center_x)
        converted.center_y = float(detection.bbox.center_y)
        converted.size_x = float(detection.bbox.size_x)
        converted.size_y = float(detection.bbox.size_y)
        return converted


def main(args=None) -> None:
    rclpy.init(args=args)
    node = YoloDetectionBridge()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
