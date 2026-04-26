---
title: ZBar ROS
description: zbar_ros - ZBar-based QR and barcode recognition with structured 2D outputs.
---

## Role

`perception/zbar_ros` is a pure 2D QR and barcode recognition module set. It turns
images into structured recognition results without mixing in task-specific semantics.

It does not currently handle:

- depth estimation
- 3D pose recovery
- target tracking
- auto-aim task logic

That makes it a general image-facing recognition front-end rather than a task
pipeline like `rm_auto_aim`.

## Package Structure

This directory contains two ROS 2 packages:

| Package | Role |
| --- | --- |
| `zbar_ros` | C++ detector node, debug-image publisher, and offline dataset helper |
| `zbar_interfaces` | message definitions for barcode detections |

Key entry points:

- Node implementation: [barcode_reader_node.cpp](https://github.com/Venom-Algorithm/Venom_VNV/blob/master/perception/zbar_ros/src/barcode_reader_node.cpp)
- Launch entry: [zbar_ros.launch.py](https://github.com/Venom-Algorithm/Venom_VNV/blob/master/perception/zbar_ros/launch/zbar_ros.launch.py)
- Offline smoke-test launch: [dataset_barcode.launch.py](https://github.com/Venom-Algorithm/Venom_VNV/blob/master/perception/zbar_ros/launch/dataset_barcode.launch.py)
- Package README: [perception/zbar_ros/README.md](https://github.com/Venom-Algorithm/Venom_VNV/blob/master/perception/zbar_ros/README.md)

## Data Flow

```text
/image_raw
  -> zbar_ros
  -> /perception/barcodes
  -> upper-layer task logic or visualization

/image_raw
  -> zbar_ros
  -> /perception/debug/barcodes
  -> RViz / rqt_image_view
```

## Inputs And Outputs

Default interfaces:

| Direction | Topic | Type | Notes |
| --- | --- | --- | --- |
| subscribe | `/image_raw` | `sensor_msgs/msg/Image` | input image |
| publish | `/perception/barcodes` | `zbar_interfaces/msg/BarcodeDetections` | per-frame recognition results |
| publish | `/perception/debug/barcodes` | `sensor_msgs/msg/Image` | annotated debug image |

Additional rules:

- `BarcodeDetections.header` is copied from the input image header
- `header.stamp` stays aligned with the source image timestamp
- `header.frame_id` stays aligned with the source image frame
- the node does not subscribe to `/camera_info`

## TF Contract

`zbar_ros` publishes no TF.

That is the correct contract for the current scope:

- the output is only a 2D image-plane recognition result
- a decoded QR or barcode from a monocular image is not a trustworthy 3D pose by itself
- camera-frame ownership should remain with the upstream driver or `venom_robot_description`

The expected integration pattern is:

1. keep detection messages in the source image frame
2. do not synthesize new `camera_*` or `target_*` TF frames here
3. if pose estimation is needed later, add a separate stage with explicit intrinsics and its own TF contract

## Message Definitions

### `BarcodeDetection.msg`

| Field | Meaning |
| --- | --- |
| `data` | decoded string content |
| `symbology` | ZBar symbol type such as `QRCODE` |
| `polygon` | 2D polygon in image pixel coordinates |

### `BarcodeDetections.msg`

| Field | Meaning |
| --- | --- |
| `header` | timestamp and frame for the current result frame |
| `detections` | all detections from the current image |

## Parameters

The detector node currently declares these parameters:

| Parameter | Meaning | Default |
| --- | --- | --- |
| `publish_debug_image` | whether to publish annotated debug images | `true` |
| `qrcode_only` | whether to restrict scanning to QR codes only | `true` |

## Launch Arguments

### `zbar_ros.launch.py`

| Launch Arg | Meaning | Default |
| --- | --- | --- |
| `image_topic` | input image topic | `"/image_raw"` |
| `detections_topic` | output detections topic | `"/perception/barcodes"` |
| `debug_image_topic` | debug image topic | `"/perception/debug/barcodes"` |
| `publish_debug_image` | whether to publish debug images | `"true"` |
| `qrcode_only` | whether to scan QR codes only | `"true"` |

### `dataset_barcode.launch.py`

| Launch Arg | Meaning | Default |
| --- | --- | --- |
| `dataset_path` | offline test image directory | `share/zbar_ros/data/dataset` |
| `image_topic` | image topic shared by publisher and detector | `"/perception/test/image_raw"` |
| `detections_topic` | output detections topic | `"/perception/barcodes"` |
| `debug_image_topic` | debug image topic | `"/perception/debug/barcodes"` |
| `frame_id` | frame id stamped into offline images | `"dataset_camera_optical_frame"` |
| `publish_interval_seconds` | publish interval | `"1.0"` |
| `publish_debug_image` | whether to publish debug images | `"true"` |
| `qrcode_only` | whether to scan QR codes only | `"true"` |

Notes:

- `dataset_camera_optical_frame` is an offline-test frame only and is not part of the runtime TF tree
- on a real robot, `frame_id` should come from the upstream camera driver and `zbar_ros` should only forward it

## Dependencies And Build

Runtime dependencies:

- `rclcpp`
- `sensor_msgs`
- `cv_bridge`
- `OpenCV`
- `zbar`
- `zbar_interfaces`

Install dependencies first:

```bash
cd ~/venom_ws
rosdep install -r --from-paths src --ignore-src --rosdistro $ROS_DISTRO -y
```

Then build the packages:

```bash
cd ~/venom_ws
colcon build --packages-select zbar_interfaces zbar_ros
source install/setup.bash
```

## Recommended Launch

Against a live camera:

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch zbar_ros zbar_ros.launch.py
```

Offline dataset smoke test:

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch zbar_ros dataset_barcode.launch.py
```

To override the camera topic:

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch zbar_ros zbar_ros.launch.py image_topic:=/camera/image_raw
```

## Verification

The minimum acceptance checklist is:

1. `colcon build --packages-select zbar_interfaces zbar_ros` passes
2. `ros2 launch zbar_ros dataset_barcode.launch.py` starts correctly
3. `/perception/barcodes` publishes `zbar_interfaces/msg/BarcodeDetections`
4. `/perception/debug/barcodes` publishes annotated debug images
5. `zbar_ros` publishes no TF

## Boundaries

Keep the boundaries explicit:

| Module | Responsible For | Not Responsible For |
| --- | --- | --- |
| `zbar_ros` | pure 2D QR/barcode recognition and structured polygon output | pose estimation, TF publishing, tracking, task decisions |
| upper layers | filtering, association, and behavior based on recognition results | pushing task semantics back into the detector message |

If code-pose estimation is needed later, keep it layered:

1. `zbar_ros` continues to publish pure recognition results
2. a separate node consumes the detections plus calibration data and performs pose estimation

## Related Pages

- [Perception](index.md)
- [YOLO Detector](yolo_detector.md)
- [Hikrobot Camera Driver](../drivers/ros2_hik_camera.md)
- [Topic Reference](../standards/topics.md)
- [TF Tree](../standards/tf_tree.md)
