# zbar_ros

`zbar_ros` is the Venom perception-layer barcode detector built on top of ZBar.
It is intended for QR code recognition first, but it can be switched to broader
barcode decoding when needed.

The integration contract is intentionally narrow:

- input stays on standard `sensor_msgs/msg/Image`
- output is published as a structured detection message, not raw strings
- no TF is published
- output headers inherit the source image `stamp` and `frame_id`

That keeps `zbar_ros` aligned with the rest of the `perception/` layer: pure 2D
recognition in, structured 2D observations out.

## Package Layout

This module lives under `perception/zbar_ros`, but it is split into two ROS 2 packages:

| Package | Role |
| --- | --- |
| `zbar_ros` | detector node, debug image publisher, and offline dataset helper |
| `zbar_interfaces` | structured detection messages used by the detector output |

## Runtime Contract

### Topics

Default runtime interfaces:

| Direction | Topic | Type | Notes |
| --- | --- | --- | --- |
| subscribe | `/image_raw` | `sensor_msgs/msg/Image` | source image stream |
| publish | `/perception/barcodes` | `zbar_interfaces/msg/BarcodeDetections` | per-frame barcode detections |
| publish | `/perception/debug/barcodes` | `sensor_msgs/msg/Image` | annotated debug image |

`BarcodeDetections.header` is copied from the input image header.
Each `BarcodeDetection` contains:

- `data`: decoded string content
- `symbology`: ZBar symbol type such as `QRCODE`
- `polygon`: 2D polygon in image pixel coordinates

### Header And Frame Rules

- `header.stamp` is copied from the input image
- `header.frame_id` is copied from the input image
- the detector does not rename frames and does not synthesize a new camera frame
- downstream consumers must treat the result as image-plane data, not as a 3D pose

### TF Contract

This module does not publish any TF frame.

That is intentional:

- decoding a barcode from a monocular image does not imply a trustworthy 3D pose
- frame ownership stays with the source camera driver or robot description package
- if pose estimation is needed later, it should be added as a separate stage with explicit camera intrinsics and its own TF contract

## Launch Files

Two launch entries are provided:

| Launch File | Purpose |
| --- | --- |
| `zbar_ros.launch.py` | run the detector against an existing camera topic |
| `dataset_barcode.launch.py` | offline smoke test using images from a local dataset directory |

### Live Camera Launch

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch zbar_ros zbar_ros.launch.py
```

Useful launch arguments:

- `image_topic`: input image topic, default `/image_raw`
- `detections_topic`: detection output topic, default `/perception/barcodes`
- `debug_image_topic`: annotated image topic, default `/perception/debug/barcodes`
- `publish_debug_image`: whether to publish annotated images, default `true`
- `qrcode_only`: when `true`, only QR codes are scanned, default `true`

Example with an explicit camera topic:

```bash
ros2 launch zbar_ros zbar_ros.launch.py image_topic:=/camera/image_raw
```

### Offline Dataset Launch

This launch file is intended for quick verification without a live camera:

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch zbar_ros dataset_barcode.launch.py
```

The launch file uses the sample image under `perception/zbar_ros/data/dataset` by default.
To override it:

```bash
ros2 launch zbar_ros dataset_barcode.launch.py \
  dataset_path:=/path/to/your/dataset \
  publish_interval_seconds:=0.5
```

The dataset helper publishes a test-only `frame_id` named
`dataset_camera_optical_frame` by default. It is only for offline verification
and is not part of the runtime TF tree.

You can also run the dataset publisher alone:

```bash
ros2 run zbar_ros dataset_image_publisher --ros-args \
  -p dataset_path:=/path/to/your/dataset
```

## Build

From `~/venom_ws`:

```bash
rosdep install -r --from-paths src --ignore-src --rosdistro $ROS_DISTRO -y
colcon build --packages-select zbar_interfaces zbar_ros
source install/setup.bash
```

## Verification

A minimal review-friendly verification flow is:

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch zbar_ros dataset_barcode.launch.py
```

In another shell:

```bash
cd ~/venom_ws
source install/setup.bash
ros2 topic echo /perception/barcodes --once
```

What to verify:

- the launch starts both `dataset_image_publisher` and `qr_code_detector`
- `/perception/barcodes` publishes `zbar_interfaces/msg/BarcodeDetections`
- `/perception/debug/barcodes` publishes annotated `sensor_msgs/msg/Image`
- detection messages preserve the source image `header`
- no TF frames are created by `zbar_ros`

## Runtime Notes

- The detector publishes one `BarcodeDetections` message per input frame, even when no code is present.
- Debug images preserve the incoming header and are safe to inspect in RViz or `rqt_image_view`.
- `qrcode_only=true` is the recommended default for the current Venom use case.
- The module does not subscribe to `/camera_info`, because the current scope is 2D decoding only.
