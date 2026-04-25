---
title: YOLO Detector
description: yolo_detector - General YOLO-based 2D detection module and message set.
---

## Module Role

`perception/yolo_detector` is a general 2D object-detection module set that turns images into YOLO-style detection outputs.

It does not currently provide:

- depth estimation
- 3D pose recovery
- multi-object tracking
- task-specific auto-aim semantics

That means it should be treated as a generic detector package, not as a full task pipeline like `rm_auto_aim`.

## Package Layout

The directory currently contains two ROS 2 packages:

| Package | Role |
| --- | --- |
| `yolo_detector` | Python detector node that loads the YOLO model, subscribes to images, and publishes detections |
| `yolo_interfaces` | message definitions for bounding boxes, class hypotheses, and per-frame detections |

Code entry points:

- Node implementation: [yolo_node.py](https://github.com/Venom-Algorithm/Venom_VNV/blob/master/perception/yolo_detector/yolo_detector/yolo_node.py)
- Launch entry: [yolo_detector.launch.py](https://github.com/Venom-Algorithm/Venom_VNV/blob/master/perception/yolo_detector/launch/yolo_detector.launch.py)
- Default parameters: [yolo_detector.yaml](https://github.com/Venom-Algorithm/Venom_VNV/blob/master/perception/yolo_detector/config/yolo_detector.yaml)

## Data Flow

```text
/image_raw
  -> yolo_detector
  -> /perception/detections
  -> upper-layer task or visualization modules

/image_raw
  -> yolo_detector
  -> /perception/debug/yolo_result
  -> RViz / rqt_image_view
```

## Topics

Default interfaces:

| Direction | Topic | Message type | Description |
| --- | --- | --- | --- |
| subscribe | `/image_raw` | `sensor_msgs/msg/Image` | input image |
| publish | `/perception/detections` | `yolo_interfaces/msg/YoloDetections` | per-frame detection output |
| publish | `/perception/debug/yolo_result` | `sensor_msgs/msg/Image` | annotated debug image |

Additional notes:

- `YoloDetections.header` is copied from the input image header
- `header.stamp` follows the image timestamp
- `header.frame_id` follows the image frame
- the node does not currently subscribe to `camera_info`

## Message Definitions

### `YoloBox.msg`

| Field | Meaning |
| --- | --- |
| `center_x` | bounding-box center x in pixels |
| `center_y` | bounding-box center y in pixels |
| `size_x` | bounding-box width in pixels |
| `size_y` | bounding-box height in pixels |

The node uses pixel-space `xywh`, not corner coordinates.

### `YoloHypothesis.msg`

| Field | Meaning |
| --- | --- |
| `class_id` | model output class id |
| `class_name` | resolved class name |
| `score` | confidence score |

### `YoloDetection.msg`

| Field | Meaning |
| --- | --- |
| `hypothesis` | class information for one object |
| `bbox` | 2D bounding box for one object |

### `YoloDetections.msg`

| Field | Meaning |
| --- | --- |
| `header` | timestamp and frame for the current image |
| `detections` | all detections in the frame |

## Parameters

The node currently declares these parameters:

| Parameter | Meaning | Default |
| --- | --- | --- |
| `detector_name` | detector name string used as a configuration label; it is not part of the published output logic right now | `"yolo_detector"` |
| `model_path` | YOLO model path, either a local `.pt` file or a model name that Ultralytics can resolve | `"yolov8n.pt"` |
| `image_topic` | input image topic | `"/image_raw"` |
| `output_topic` | output detection topic | `"/perception/detections"` |
| `annotated_image_topic` | debug image topic | `"/perception/debug/yolo_result"` |
| `publish_annotated_image` | whether to publish the annotated debug image; disabling it can reduce bandwidth and CPU cost | `true` |
| `confidence_threshold` | confidence threshold passed to YOLO inference | `0.25` |
| `iou_threshold` | IoU threshold passed to YOLO inference / NMS | `0.45` |
| `device` | inference device string; empty lets Ultralytics choose automatically, otherwise values like `cpu` or `0` can be passed | `""` |
| `class_ids` | comma-separated class filter list such as `0,2,5`; empty means no class filtering | `""` |

## Launch Arguments

The current launch file exposes three arguments:

| Launch argument | Meaning | Default |
| --- | --- | --- |
| `model_path` | model path | `"yolov8n.pt"` |
| `image_topic` | input image topic | `"/image_raw"` |
| `output_topic` | output detections topic | `"/perception/detections"` |

Important detail:

- the current [yolo_detector.launch.py](https://github.com/Venom-Algorithm/Venom_VNV/blob/master/perception/yolo_detector/launch/yolo_detector.launch.py) only forwards these three values to the node
- `annotated_image_topic`, `publish_annotated_image`, `confidence_threshold`, `iou_threshold`, `device`, and `class_ids` are already declared in the node, but are not separately exposed in the default launch file
- if you need to override them temporarily, use `ros2 run ... --ros-args -p ...`, or extend the launch file later

## Dependencies and Build

Runtime dependencies include:

- `rclpy`
- `sensor_msgs`
- `std_msgs`
- `cv_bridge`
- `ultralytics`
- `yolo_interfaces`

Recommended dependency installation:

```bash
cd ~/venom_ws
rosdep install -r --from-paths src --ignore-src --rosdistro $ROS_DISTRO -y
```

If `rosdep` does not install `ultralytics` correctly in the current environment, use the manual fallback:

```bash
python3 -m pip install -U ultralytics
```

Then build the two packages:

```bash
cd ~/venom_ws
colcon build --packages-select yolo_interfaces yolo_detector
source install/setup.bash
```

## Recommended Commands

Launch-based run:

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch yolo_detector yolo_detector.launch.py model_path:=/path/to/model.pt
```

Direct node run:

```bash
cd ~/venom_ws
source install/setup.bash
ros2 run yolo_detector yolo_node
```

Direct node run with more parameter overrides:

```bash
cd ~/venom_ws
source install/setup.bash
ros2 run yolo_detector yolo_node --ros-args \
  -p model_path:=/path/to/model.pt \
  -p image_topic:=/camera/image_raw \
  -p output_topic:=/perception/detections \
  -p publish_annotated_image:=false \
  -p confidence_threshold:=0.4 \
  -p class_ids:="0,1"
```

## Engineering Boundary

The separation between `yolo_detector` and `rm_auto_aim` should stay explicit:

| Module | Owns | Does not own |
| --- | --- | --- |
| `yolo_detector` | generic 2D detections, class labels, bounding boxes | tracking, ballistics, auto-aim control |
| `rm_auto_aim` | target-specific detection, tracking, ballistics, control outputs | generic YOLO detector abstraction |

If YOLO detections are later connected to task logic, the cleaner layering is:

1. keep `yolo_detector` as a pure detector
2. let upper layers handle semantic mapping, filtering, tracking, and decision logic

## Typical Use Cases

This package is a good fit for:

- generic detection baseline validation
- UAV or UGV 2D vision front-end work
- providing pure detection inputs to upper mission layers
- quickly swapping YOLO weights without coupling the detector to task semantics

## Related Pages

- [Perception](index.md)
- [Hikrobot Camera Driver](../drivers/ros2_hik_camera.md)
- [Auto Aim Overview](../auto_aim/index.md)
- [Topic Reference](../standards/topics.md)
