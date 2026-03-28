# venom_serial_driver

DJI C-board serial communication driver for the RoboMaster robot vision system.

## Features

- Bidirectional binary protocol implementation
- CRC16 data verification
- Sliding-window frame parsing
- Timeout protection
- ROS 2 topic interface

## Installation

```bash
cd ~/venom_ws
colcon build --packages-select venom_serial_driver
source install/setup.bash
```

## Usage

### Launch the driver

```bash
ros2 launch venom_serial_driver serial_driver.launch.py
```

### Override serial parameters

```bash
ros2 launch venom_serial_driver serial_driver.launch.py \
  port_name:=/dev/ttyUSB0 \
  baud_rate:=921600
```

## ROS 2 Topics

Full system-level topic reference: [topics.md](./topics.md)

### Subscriptions

| Topic | Message Type | Description |
|---|---|---|
| `/cmd_vel` | `geometry_msgs/Twist` | Chassis velocity command. Only `linear.x/y/z` are used. |
| `/auto_aim` | `venom_serial_driver/AutoAimCmd` | Gimbal angle commands and aim state (pitch, yaw, detected, tracking, fire, distance, proj_x/y). |

### Publications

| Topic | Message Type | Description |
|---|---|---|
| `/robot_status` | `venom_serial_driver/RobotStatus` | Chassis velocity and gimbal angle feedback from C-board. |
| `/game_status` | `venom_serial_driver/GameStatus` | Game state: HP, barrel heat, game progress, RFID, etc. |

## Parameter Configuration

Edit `config/serial_params.yaml`:

```yaml
serial_node:
  ros__parameters:
    port_name: "/dev/ttyUSB0"  # serial device
    baud_rate: 921600           # baud rate
    timeout: 0.1                # read timeout (s)
    loop_rate: 50               # timer frequency (Hz)
```

## Communication Protocol

See [protocol.md](protocol.md) for the full binary protocol specification.

### Frame Format

**NUC -> C-board (control command)**
```
[0xA5][len(2)][0x02][data][CRC16(2)]
```

**C-board -> NUC (state data)**
```
[0x5A][len(2)][0x01][data][CRC16(2)]
```

## Testing

### Monitor incoming state data

```bash
ros2 topic echo /robot_status
ros2 topic echo /game_status
```

### Send a chassis velocity command

```bash
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist \
  '{linear: {x: 0.1, y: 0.0, z: 0.0}}'
```

### Send an auto-aim command

```bash
ros2 topic pub /auto_aim venom_serial_driver/msg/AutoAimCmd \
  '{pitch: 0.1, yaw: 0.2, detected: true, tracking: true, fire: false, distance: 3.0, proj_x: 640, proj_y: 360}'
```

### Hardware tests (requires physical serial connection)

```bash
# Loopback and CRC validation
python3 test/test_loopback.py /dev/ttyUSB0

# Real-time state monitor (no ROS stack required)
python3 test/test_monitor.py --port /dev/ttyUSB0

# Yaw rotation test
python3 test/test_hardware.py --port /dev/ttyUSB0 --test yaw

# Chassis motion test
python3 test/test_hardware.py --port /dev/ttyUSB0 --test chassis
```

## Troubleshooting

1. **Serial permission denied**
   ```bash
   sudo chmod 666 /dev/ttyUSB0
   ```

2. **Check serial device**
   ```bash
   ls /dev/ttyUSB*
   ```

3. **Enable debug logging**
   ```bash
   ros2 run venom_serial_driver serial_node --ros-args --log-level debug
   ```
