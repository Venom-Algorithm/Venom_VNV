# Read Meter Service Plugin

本文档说明 `venom_mission_commander` 中 `read_meter` 任务插件的 service 接入方式。

核心边界：`MissionCommander` 只负责任务编排；`ReadMeterTaskPlugin` 在需要真实读数时调用外部 service；具体视觉算法由 perception 节点实现。

```text
waypoint tasks
→ read_meter plugin
→ /perception/read_printed_number
→ blackboard["meter_reading"]
→ voice_report
```

## Plugin Location

| Item | Value |
| --- | --- |
| class | `ReadMeterTaskPlugin` |
| file | `venom_mission_commander/task_plugins.py` |
| task type | `read_meter` |
| default output key | `meter_reading` |

`task_type` 保持为 `read_meter`，所以现有 mission YAML 不需要改任务类型。

## Backends

### `backend: mock`

默认行为。未配置 `backend` 时仍走 mock，保证旧 mission 不受影响：

```yaml
- name: read_meter_at_point_2
  type: read_meter
  meter_id: example_meter
  mock_value: 220.0V
  mock_confidence: 0.9
  mock_delay_sec: 0.3
```

输出写入：

```python
blackboard["meter_reading"] = {
    "meter_id": "example_meter",
    "value": "220.0V",
    "confidence": 0.9,
}
```

### `backend: service`

真实读纸上数字时使用。插件调用 `printed_number_interfaces/srv/ReadPrintedNumber`：

```yaml
- name: read_printed_number
  type: read_meter
  backend: service
  service_name: /perception/read_printed_number
  meter_id: meter_1
  expected_digits: 4
  timeout_sec: 5.0
  min_confidence: 0.7
  output_key: meter_reading
```

成功后写入：

```python
blackboard["meter_reading"] = {
    "meter_id": "meter_1",
    "value": "1234",
    "confidence": 1.0,
    "source": "printed_number_service",
}
```

## YAML Parameters

| Parameter | Default | Backend | Notes |
| --- | --- | --- | --- |
| `backend` | `mock` | all | 支持 `mock` / `service` |
| `meter_id` | `meter_1` | all | 目标 ID，会传给 service |
| `mock_value` | `220.0V` | mock | mock 返回值 |
| `mock_confidence` | `0.9` | mock | mock 置信度 |
| `mock_delay_sec` | `0.5` | mock | mock 等待时间 |
| `service_name` | `/perception/read_printed_number` | service | 数字读取 service |
| `timeout_sec` | `5.0` | service | service 总等待时间 |
| `service_wait_timeout_sec` | `1.0` | service | 等待 service 可用的时间，上限不超过 `timeout_sec` |
| `expected_digits` | `0` | service | 期望数字位数，0 表示不限制 |
| `min_confidence` | `0.0` | service | 插件侧最低置信度校验 |
| `output_key` | `meter_reading` | service | 写入 blackboard 的 key |

## Service Contract

插件调用：

```srv
string target_id
float32 timeout_sec
uint32 expected_digits
float32 min_confidence
---
bool success
string value
float32 confidence
string message
```

插件侧会额外校验：

- service 是否可用
- service 是否超时
- `response.success` 是否为 true
- `response.value` 是否为纯数字
- `expected_digits` 是否匹配
- `response.confidence` 是否达到 `min_confidence`

任一校验失败都会返回 `TaskExecutionResult(False, message)`。如果 mission 配置了 `stop_on_task_failure: true`，该 waypoint 后续任务不会继续执行。

## Example Mission

已提供最小示例：

```text
config/printed_number_service_mission.yaml
```

运行前先启动 reader：

```bash
cd ~/venom_ws
source install/setup.bash
ros2 launch printed_number_reader printed_number_reader.launch.py
```

再运行 mission：

```bash
ros2 run venom_mission_commander mission_commander --ros-args \
  -p mission_config:=/home/alex/venom_ws/src/venom_vnv/venom_mission_commander/config/printed_number_service_mission.yaml
```

预期流程：

```text
wait_before_read
→ read_printed_number
→ writes blackboard["meter_reading"]
→ voice_report_printed_number
→ mission_completed
```

## 5-Terminal YOLO Verification

每个终端先执行：

```bash
cd ~/venom_ws
source install/setup.bash
```

Terminal 1，启动 USB 摄像头：

```bash
ros2 run v4l2_camera v4l2_camera_node --ros-args \
  -p video_device:=/dev/v4l/by-id/usb-SunplusIT_Inc_FHD_Webcam_01.00.00-video-index0 \
  -p pixel_format:=YUYV \
  -p output_encoding:=bgr8 \
  -p image_size:="[640, 480]" \
  -r image_raw:=/image_raw
```

Terminal 2，启动 4 位数字 YOLO：

```bash
ros2 run yolo_detector yolo_node --ros-args \
  -p model_path:=/home/alex/venom_ws/models/yolo/yolo_26_detect_digit.pt \
  -p image_topic:=/image_raw \
  -p output_topic:=/perception/digit_detections \
  -p annotated_image_topic:=/perception/debug/digit_yolo_result \
  -p confidence_threshold:=0.25 \
  -p device:=cpu
```

Terminal 3，启动数字读取 service：

```bash
ros2 run printed_number_reader printed_number_reader_node --ros-args \
  -p reader_mode:=yolo \
  -p detections_topic:=/perception/digit_detections \
  -p expected_digits:=4 \
  -p min_confidence:=0.25
```

Terminal 4，直接验证 service：

```bash
ros2 service call /perception/read_printed_number printed_number_interfaces/srv/ReadPrintedNumber \
"{target_id: test, timeout_sec: 5.0, expected_digits: 4, min_confidence: 0.25}"
```

Terminal 5，验证 mission 插件链路：

```bash
ros2 run venom_mission_commander mission_commander --ros-args \
  -p mission_config:=/home/alex/venom_ws/src/venom_vnv/venom_mission_commander/config/printed_number_service_mission.yaml
```

## Notes

- 不要把 YOLO/OCR 逻辑写进 `MissionCommander` 主流程；保持 service 边界稳定。
- 默认 mock backend 是兼容层，方便没有视觉节点时继续验证任务编排。
- 如果后续识别算法从 YOLO 换成 OCR，只要继续提供 `/perception/read_printed_number`，插件侧通常不需要改。
