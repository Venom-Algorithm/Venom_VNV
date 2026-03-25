"""
DJI C-board 通信协议实现
基于 vision_comm.h 和协议文档
"""
import struct
from .crc_utils import crc16, verify_crc16, append_crc16

# 协议常量
SOF_TX = 0xA5  # NUC发送给C板
SOF_RX = 0xA5  # C板发送给NUC
CMD_ID_STATE = 0x01  # C板状态数据
CMD_ID_CTRL = 0x02   # 视觉控制指令


class RobotCtrlData:
    """机器人控制数据 (NUC → C板) - 33字节格式"""
    def __init__(self):
        self.flags = 0  # 控制标志位
        self.lx = 0.0
        self.ly = 0.0
        self.lz = 0.0
        self.ax = 0.0
        self.ay = 0.0
        self.az = 0.0
        self.dist = 0.0
        self.frame_x = 0
        self.frame_y = 0

    def pack(self) -> bytes:
        """打包为字节流 (小端序) - 格式: <B7f2H"""
        return struct.pack('<B7f2H',
                          self.flags,
                          self.lx, self.ly, self.lz,
                          self.ax, self.ay, self.az,
                          self.dist,
                          self.frame_x, self.frame_y)


class RobotStateData:
    """机器人状态数据 (C板 → NUC)"""
    def __init__(self):
        self.timestamp_us = 0
        self.linear_x = 0.0
        self.linear_y = 0.0
        self.linear_z = 0.0
        self.gyro_wz = 0.0
        self.angular_y = 0.0
        self.angular_z = 0.0
        self.angular_y_speed = 0.0
        self.angular_z_speed = 0.0
        self.distance = 0.0
        self.game_progress = 0
        self.stage_remain_time = 0
        self.center_outpost_occupancy = 0
        self.current_HP = 0
        self.maximum_HP = 0
        self.shooter_barrel_heat_limit = 0
        self.power_management = 0
        self.shooter_17mm_barrel_heat = 0
        self.shooter_42mm_barrel_heat = 0
        self.armor_id = 0
        self.HP_deduction_reason = 0
        self.launching_frequency = 0.0
        self.initial_speed = 0.0
        self.projectile_allowance_17mm = 0
        self.projectile_allowance_42mm = 0
        self.rfid_status = 0

    @staticmethod
    def unpack(data: bytes):
        """从字节流解包 (小端序) - 72字节格式"""
        if len(data) < 72:
            return None

        state = RobotStateData()
        unpacked = struct.unpack('<I9fBHB3HB2HB2f2HI', data[:72])

        state.timestamp_us = unpacked[0]
        state.linear_x = unpacked[1]
        state.linear_y = unpacked[2]
        state.linear_z = unpacked[3]
        state.gyro_wz = unpacked[4]
        state.angular_y = unpacked[5]
        state.angular_z = unpacked[6]
        state.angular_y_speed = unpacked[7]
        state.angular_z_speed = unpacked[8]
        state.distance = unpacked[9]
        state.game_progress = unpacked[10] & 0x0F
        state.stage_remain_time = unpacked[11]
        state.center_outpost_occupancy = unpacked[12] & 0x03
        state.current_HP = unpacked[13]
        state.maximum_HP = unpacked[14]
        state.shooter_barrel_heat_limit = unpacked[15]
        state.power_management = unpacked[16]
        state.shooter_17mm_barrel_heat = unpacked[17]
        state.shooter_42mm_barrel_heat = unpacked[18]
        state.armor_id = unpacked[19] & 0x0F
        state.HP_deduction_reason = (unpacked[19] >> 4) & 0x0F
        state.launching_frequency = unpacked[20]
        state.initial_speed = unpacked[21]
        state.projectile_allowance_17mm = unpacked[22]
        state.projectile_allowance_42mm = unpacked[23]
        state.rfid_status = unpacked[24]

        return state


def pack_ctrl_frame(ctrl_data: RobotCtrlData) -> bytes:
    """打包控制帧 (NUC → C板)"""
    data = ctrl_data.pack()
    frame = struct.pack('<BHB', SOF_TX, len(data), CMD_ID_CTRL) + data
    return append_crc16(frame)


def unpack_state_frame(raw_bytes: bytes) -> tuple:
    """解析状态帧 (C板 → NUC)，返回 (success, state_data)"""
    if len(raw_bytes) < 6:
        return False, None

    if raw_bytes[0] != SOF_RX:
        return False, None

    data_len = struct.unpack('<H', raw_bytes[1:3])[0]  # 小端序
    cmd_id = raw_bytes[3]
    frame_len = 4 + data_len + 2

    if len(raw_bytes) < frame_len:
        return False, None

    if not verify_crc16(raw_bytes[:frame_len]):
        return False, None

    if cmd_id != CMD_ID_STATE:
        return False, None

    state = RobotStateData.unpack(raw_bytes[4:4+data_len])
    return True, state


