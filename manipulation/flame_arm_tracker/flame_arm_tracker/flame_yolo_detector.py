from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from ament_index_python.packages import get_package_share_directory
import cv2
from cv_bridge import CvBridge
import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from venom_manipulation_interfaces.msg import Detection2D, Detection2DArray

try:
    import openvino as ov
except Exception:  # pragma: no cover - optional acceleration path
    ov = None

try:
    from ultralytics import YOLO
except Exception:  # pragma: no cover - reported at runtime in __init__
    YOLO = None

try:
    import yaml
except Exception:  # pragma: no cover - metadata is optional
    yaml = None


class OpenVinoRuntimeDetector:
    def __init__(self, model_path: Path, fallback_class_names: Sequence[str]) -> None:
        if ov is None:
            raise RuntimeError("openvino is not importable")

        xml_files = sorted(model_path.glob("*.xml"))
        if not xml_files:
            raise RuntimeError("no OpenVINO .xml file found in %s" % model_path)

        self.names = self._load_names(model_path, fallback_class_names)
        self.core = ov.Core()
        self.compiled_model = self.core.compile_model(str(xml_files[0]), "CPU")
        self.input = self.compiled_model.inputs[0]
        self.output = self.compiled_model.outputs[0]
        shape = list(self.input.shape)
        if len(shape) != 4:
            raise RuntimeError("unsupported OpenVINO input shape: %s" % shape)
        self.input_h = int(shape[2])
        self.input_w = int(shape[3])

    def detect(
        self,
        bgr_image,
        header,
        confidence_threshold: float,
        iou_threshold: float,
        allowed_class_names,
    ) -> List[Detection2D]:
        tensor, ratio, pad_x, pad_y = self._preprocess(bgr_image)
        raw = self.compiled_model([tensor])[self.output]
        rows = np.squeeze(raw)
        if rows.ndim != 2 or rows.shape[1] < 6:
            return []

        image_h, image_w = bgr_image.shape[:2]
        candidates: List[Detection2D] = []
        nms_boxes: List[List[int]] = []
        scores: List[float] = []

        for row in rows:
            confidence = float(row[4])
            if confidence < confidence_threshold:
                continue

            class_id = int(round(float(row[5])))
            class_name = self.names.get(class_id, str(class_id))
            if allowed_class_names and class_name not in allowed_class_names:
                continue

            x1, y1, x2, y2 = [float(value) for value in row[:4]]
            x1 = (x1 - pad_x) / ratio
            x2 = (x2 - pad_x) / ratio
            y1 = (y1 - pad_y) / ratio
            y2 = (y2 - pad_y) / ratio
            x1 = min(max(x1, 0.0), float(image_w - 1))
            x2 = min(max(x2, 0.0), float(image_w - 1))
            y1 = min(max(y1, 0.0), float(image_h - 1))
            y2 = min(max(y2, 0.0), float(image_h - 1))
            width = x2 - x1
            height = y2 - y1
            if width <= 1.0 or height <= 1.0:
                continue

            detection = Detection2D()
            detection.header = header
            detection.class_name = class_name
            detection.confidence = confidence
            detection.center_x = (x1 + x2) * 0.5
            detection.center_y = (y1 + y2) * 0.5
            detection.size_x = width
            detection.size_y = height
            candidates.append(detection)
            nms_boxes.append([int(round(x1)), int(round(y1)), int(round(width)), int(round(height))])
            scores.append(confidence)

        if not candidates:
            return []

        selected = cv2.dnn.NMSBoxes(nms_boxes, scores, confidence_threshold, iou_threshold)
        if len(selected) == 0:
            return []
        selected_indices = np.array(selected).reshape(-1).tolist()
        detections = [candidates[index] for index in selected_indices]
        detections.sort(key=lambda detection: detection.confidence, reverse=True)
        return detections

    def _preprocess(self, bgr_image) -> Tuple[np.ndarray, float, float, float]:
        image_h, image_w = bgr_image.shape[:2]
        ratio = min(self.input_w / float(image_w), self.input_h / float(image_h))
        resized_w = int(round(image_w * ratio))
        resized_h = int(round(image_h * ratio))
        resized = cv2.resize(bgr_image, (resized_w, resized_h), interpolation=cv2.INTER_LINEAR)

        canvas = np.full((self.input_h, self.input_w, 3), 114, dtype=np.uint8)
        pad_x = (self.input_w - resized_w) / 2.0
        pad_y = (self.input_h - resized_h) / 2.0
        left = int(round(pad_x))
        top = int(round(pad_y))
        canvas[top : top + resized_h, left : left + resized_w] = resized

        rgb_image = cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)
        tensor = rgb_image.transpose(2, 0, 1)[None].astype(np.float32) / 255.0
        return tensor, ratio, float(left), float(top)

    def _load_names(self, model_path: Path, fallback_class_names: Sequence[str]) -> Dict[int, str]:
        metadata_path = model_path / "metadata.yaml"
        if yaml is not None and metadata_path.exists():
            with metadata_path.open("r", encoding="utf-8") as stream:
                metadata = yaml.safe_load(stream) or {}
            names = metadata.get("names") or {}
            return {int(class_id): str(name) for class_id, name in names.items()}
        return {index: str(name) for index, name in enumerate(fallback_class_names)}


class FlameYoloDetector(Node):
    def __init__(self) -> None:
        super().__init__("flame_yolo_detector")

        self.declare_parameter("image_topic", "/camera/d435i/color/image_raw")
        self.declare_parameter("detection_topic", "/perception/detections_2d")
        self.declare_parameter("detection_array_topic", "/perception/detections_2d_array")
        self.declare_parameter("debug_result_topic", "/perception/debug/flame_yolo_result")
        self.declare_parameter("publish_debug_images", False)
        self.declare_parameter("model_path", "")
        self.declare_parameter("class_names", ["flame_picture", "flame", "fire"])
        self.declare_parameter("confidence_threshold", 0.45)
        self.declare_parameter("iou_threshold", 0.45)
        self.declare_parameter("image_size", 640)
        self.declare_parameter("device", "")
        self.declare_parameter("use_openvino_runtime", True)

        self.class_names = {
            str(name).strip()
            for name in self.get_parameter("class_names").value
            if str(name).strip()
        }
        self.confidence_threshold = float(self.get_parameter("confidence_threshold").value)
        self.iou_threshold = float(self.get_parameter("iou_threshold").value)
        self.image_size = int(self.get_parameter("image_size").value)
        self.device = str(self.get_parameter("device").value)
        self.publish_debug_images = bool(self.get_parameter("publish_debug_images").value)
        self.use_openvino_runtime = bool(self.get_parameter("use_openvino_runtime").value)

        self.bridge = CvBridge()
        self.openvino_model = None
        model_path = str(self.get_parameter("model_path").value)
        if self.use_openvino_runtime:
            self.openvino_model = self._load_openvino_model(model_path)
        self.model = None if self.openvino_model is not None else self._load_yolo_model(model_path)

        self.detection_pub = self.create_publisher(
            Detection2D,
            str(self.get_parameter("detection_topic").value),
            10,
        )
        self.array_pub = self.create_publisher(
            Detection2DArray,
            str(self.get_parameter("detection_array_topic").value),
            10,
        )
        self.result_pub = self.create_publisher(
            Image,
            str(self.get_parameter("debug_result_topic").value),
            10,
        )
        self.image_sub = self.create_subscription(
            Image,
            str(self.get_parameter("image_topic").value),
            self.image_callback,
            10,
        )

        self.get_logger().info(
            "Flame YOLO detector ready: model=%s classes=%s backend=%s"
            % (
                self.model_path,
                sorted(self.class_names),
                "openvino_runtime" if self.openvino_model is not None else "ultralytics",
            )
        )

    def _resolve_model_path(self, model_path: str) -> Path:
        path = Path(model_path).expanduser()
        if path.is_absolute() or path.exists():
            return path
        return Path(get_package_share_directory("flame_arm_tracker")) / path

    def _load_openvino_model(self, model_path: str):
        path = self._resolve_model_path(model_path)
        self.model_path = str(path)
        if not path.is_dir():
            return None
        try:
            detector = OpenVinoRuntimeDetector(path, sorted(self.class_names))
            self.get_logger().info(
                "Loaded OpenVINO runtime model from %s with input %dx%d"
                % (path, detector.input_w, detector.input_h)
            )
            return detector
        except Exception as exc:
            self.get_logger().warn(
                "OpenVINO runtime load failed for '%s', falling back to Ultralytics: %s"
                % (path, exc)
            )
            return None

    def _load_yolo_model(self, model_path: str):
        path = self._resolve_model_path(model_path)
        self.model_path = str(path)
        if YOLO is None:
            self.get_logger().error("ultralytics is not importable; YOLO detector disabled.")
            return None
        if not model_path:
            self.get_logger().error("YOLO model_path is empty; YOLO detector disabled.")
            return None
        if not path.exists():
            self.get_logger().error("YOLO model_path does not exist: %s" % path)
            return None
        try:
            return YOLO(str(path))
        except Exception as exc:
            self.get_logger().error("Failed to load YOLO model '%s': %s" % (path, exc))
            return None

    def image_callback(self, message: Image) -> None:
        try:
            bgr_image = self.bridge.imgmsg_to_cv2(message, desired_encoding="bgr8")
        except Exception as exc:
            self.get_logger().warn("Failed to decode image: %s" % exc)
            return

        detections: List[Detection2D] = []
        if self.openvino_model is not None or self.model is not None:
            detections = self._detect(bgr_image, message.header)

        array_message = Detection2DArray()
        array_message.header = message.header
        array_message.detections = detections
        self.array_pub.publish(array_message)
        if detections:
            self.detection_pub.publish(detections[0])

        if self.publish_debug_images:
            self._publish_debug_image(message, bgr_image, detections)

    def _detect(self, bgr_image, header) -> List[Detection2D]:
        if self.openvino_model is not None:
            return self.openvino_model.detect(
                bgr_image,
                header,
                self.confidence_threshold,
                self.iou_threshold,
                self.class_names,
            )

        kwargs = {
            "conf": self.confidence_threshold,
            "iou": self.iou_threshold,
            "imgsz": self.image_size,
            "verbose": False,
        }
        if self.device:
            kwargs["device"] = self.device
        try:
            results = self.model.predict(bgr_image, **kwargs)
        except Exception as exc:
            self.get_logger().warn("YOLO prediction failed: %s" % exc)
            return []

        if not results:
            return []
        result = results[0]
        names = result.names or {}
        detections: List[Detection2D] = []
        if result.boxes is None:
            return detections

        for box in result.boxes:
            cls_id = int(box.cls[0].item())
            class_name = str(names.get(cls_id, cls_id))
            if self.class_names and class_name not in self.class_names:
                continue

            confidence = float(box.conf[0].item())
            x1, y1, x2, y2 = [float(value) for value in box.xyxy[0].tolist()]
            detection = Detection2D()
            detection.header = header
            detection.class_name = class_name
            detection.confidence = confidence
            detection.center_x = (x1 + x2) * 0.5
            detection.center_y = (y1 + y2) * 0.5
            detection.size_x = max(0.0, x2 - x1)
            detection.size_y = max(0.0, y2 - y1)
            detections.append(detection)

        detections.sort(key=lambda detection: detection.confidence, reverse=True)
        return detections

    def _publish_debug_image(self, source_message: Image, bgr_image, detections: List[Detection2D]) -> None:
        result_image = bgr_image.copy()
        for detection in detections:
            x1 = int(round(detection.center_x - detection.size_x * 0.5))
            y1 = int(round(detection.center_y - detection.size_y * 0.5))
            x2 = int(round(detection.center_x + detection.size_x * 0.5))
            y2 = int(round(detection.center_y + detection.size_y * 0.5))
            cv2.rectangle(result_image, (x1, y1), (x2, y2), (0, 255, 255), 2)
            label = "%s %.2f" % (detection.class_name, detection.confidence)
            cv2.putText(
                result_image,
                label,
                (x1, max(0, y1 - 6)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 255),
                1,
                cv2.LINE_AA,
            )

        result_message = self.bridge.cv2_to_imgmsg(result_image, encoding="bgr8")
        result_message.header = source_message.header
        self.result_pub.publish(result_message)


def main(args: Optional[List[str]] = None) -> None:
    rclpy.init(args=args)
    node = FlameYoloDetector()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
