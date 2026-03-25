#!/usr/bin/env python3
import sys
import time
import math
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from venom_serial_driver.serial_interface import SerialInterface
from venom_serial_driver import serial_protocol


class SerialMonitor:
    def __init__(self, port, baudrate=921600):
        self.serial = SerialInterface(port, baudrate, 0.1)
        self.rx_buffer = bytearray()
        self.frame_count = 0
        self.start_time = None

    def run(self):
        """持续监听并打印"""
        if not self.serial.connect():
            print("❌ 串口连接失败")
            return

        print(f"✓ 串口已连接: {self.serial.port}")
        print("开始监听... (Ctrl+C 退出)\n")

        self.start_time = time.time()

        try:
            while True:
                data = self.serial.read_bytes(128)
                if data:
                    self.rx_buffer.extend(data)
                    self._parse_and_print()
                time.sleep(0.001)
        except KeyboardInterrupt:
            print("\n\n监听已停止")
            self._print_statistics()
        finally:
            self.serial.disconnect()

    def _parse_and_print(self):
        """解析并打印状态帧"""
        while len(self.rx_buffer) >= 6:
            if self.rx_buffer[0] != serial_protocol.SOF_RX:
                bad_byte = self.rx_buffer.pop(0)
                # print(f"[WARN] 丢弃垃圾字节: 0x{bad_byte:02X} (期望帧头: 0x{serial_protocol.SOF_RX:02X})")
                continue

            success, state = serial_protocol.unpack_state_frame(bytes(self.rx_buffer))

            if success and state:
                self.frame_count += 1
                elapsed = time.time() - self.start_time
                freq = self.frame_count / elapsed if elapsed > 0 else 0

                print(f"[{self.frame_count:05d}] "
                      f"Pitch: {state.angular_y:6.2f}° "
                      f"Yaw: {state.angular_z:6.2f}° "
                      f"HP: {state.current_HP}/{state.maximum_HP} "
                      f"Freq: {freq:.1f}Hz")

                data_len = int.from_bytes(self.rx_buffer[1:3], 'little')
                frame_len = 4 + data_len + 2
                self.rx_buffer = self.rx_buffer[frame_len:]
            else:
                # print(f"[WARN] 检测到疑似垃圾/坏帧，丢弃1字节后继续同步 (buffer_len={len(self.rx_buffer)})")
                self.rx_buffer.pop(0)

    def _print_statistics(self):
        """打印统计信息"""
        elapsed = time.time() - self.start_time
        freq = self.frame_count / elapsed if elapsed > 0 else 0
        print(f"\n统计信息:")
        print(f"  运行时间: {elapsed:.2f}s")
        print(f"  接收帧数: {self.frame_count}")
        print(f"  平均频率: {freq:.2f} Hz")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', default='/dev/ttyUSB0')
    args = parser.parse_args()

    monitor = SerialMonitor(args.port)
    monitor.run()
