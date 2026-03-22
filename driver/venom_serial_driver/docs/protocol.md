### 1. NUC发送 C板接收
**模块：** 基础运控  
**命令 ID (cmd_id)：** `0x02`

| 位 (Byte) | 字段名 | 类型 | 含义 | 单位 | 备注 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 0 | sof | uint8_t | 0xA5 | - | - |
| 1-2 | data_length | uint16_t | 数据段长度 | - | 小端 |
| 3 | cmd_id | uint8_t | 0x02 | - | - |
| 4 | armor_detected | uint8_t :1 | 是否检测到目标 | - | 0 = 未检测到 1 = 已检测到 |
| 4 | tracking_state | uint8_t :1 | 是否处于跟踪状态 | - | 0 = 丢失目标 1 = 正在跟踪 |
| 4 | fire | uint8_t :1 | 是否开火 | - | 0 = 禁止开火 1 = 允许开火 |
| 5-8 | linear_x | float32 | 底盘前后速度 | m/s | - |
| 9-12 | linear_y | float32 | 底盘左右速度 | m/s | - |
| 13-16 | linear_z | float32 | 相对于云台中心Z方向速度 | m/s | 地面机器人可置0，保留扩展 |
| 17-20 | gyro_wz | float32 | 小陀螺角速度 / 底盘旋转角速度 | rad/s | - |
| 21-24 | angular_y | float32 | 相对于云台中心的 pitch 控制量 | rad | - |
| 25-28 | angular_z | float32 | 相对于云台中心的 yaw 控制量 | rad | - |
| 29-32 | distance | float32 | 预留 float32 | - | - |
| 33-34 | frame_x | uint16_t | 目标像素 X 坐标 | - | - |
| 35-36 | frame_y | uint16_t | 目标像素 Y 坐标 | - | - |

---

### 2. C板发送 NUC接收
**模块：** 基础运控  
**命令 ID (cmd_id)：** `0x01`

| 位 (Byte) | 字段名 | 类型 | 含义 | 单位 | 备注 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 0 | sof | uint8_t | 0xA5 | - | - |
| 1-2 | data_length | uint16_t | 数据段长度 | - | 小端 |
| 3 | cmd_id | uint8_t | 0x01 | - | - |
| 4-7 | timestamp_us | uint32_t | 数据时间戳 | us | 建议新增 |
| 8-11 | linear_x | float32 | 底盘前后速度 | m/s | - |
| 12-15 | linear_y | float32 | 底盘左右速度 | m/s | - |
| 16-19 | linear_z | float32 | 相对于云台中心Z方向速度 | m/s | 地面机器人可置0，保留扩展 |
| 20-23 | gyro_wz | float32 | 小陀螺角速度 / 底盘旋转角速度 | rad/s | - |
| 24-27 | angular_y | float32 | 相对于云台中心的 pitch 控制量 | rad | - |
| 28-31 | angular_z | float32 | 相对于云台中心的 yaw 控制量 | rad | - |
| 32-35 | angular_y speed | float32 | 相对于云台中心的 pitch的速度 | rad/s | - |
| 36-39 | angular_z speed | float32 | 相对于云台中心的 yaw 的速度 | rad/s | - |
| 40-43 | distance | float32 | 预留 float32 | - | - |
| 44 | game_progress | uint8_t :4 | 当前比赛阶段 | - | 0：未开始比赛；1：准备阶段；2：自检；3：倒计时；4：比赛中；5：结算 |
| 45-46 | stage_remain_time | uint16_t | 当前阶段剩余时间 | s | - |
| 47 | center_outpost_occupancy | uint8_t :2 | 中心增益点的占领状态 | - | 0：未被占领；1：己方占领；2：对方占领；3：双方占领 |
| 48-49 | current_HP | uint16_t | 机器人当前血量 | - | - |
| 50-51 | maximum_HP | uint16_t | 机器人血量上限 | - | - |
| 52-53 | shooter_barrel_heat_limit | uint16_t | 机器人射击热量上限 | - | - |
| 54 | power_management_gimbal_output | uint8_t :1 | gimbal 口输出情况 | - | bit 0：0为无输出，1为24V输出 |
| 54 | power_management_chassis_output | uint8_t :1 | chassis 口输出情况 | - | bit 1：0为无输出，1为24V输出 |
| 54 | power_management_shooter_output | uint8_t :1 | shooter 口输出情况 | - | bit 2：0为无输出，1为24V输出 |
| 55-56 | shooter_17mm_barrel_heat | uint16_t | 17mm 发射机构射击热量 | - | - |
| 57-58 | shooter_42mm_barrel_heat | uint16_t | 42mm 发射机构射击热量 | - | - |
| 59 | armor_id | uint8_t :4 | 扣血装甲 ID | - | 攻击、撞击或离线时的装甲编号 |
| 60 | HP_deduction_reason | uint8_t :4 | 血量变化类型 | - | 0：弹丸攻击；1：模块离线；5：受撞击 |
| 61-64 | launching_frequency | float32 | 弹丸射速 | Hz | - |
| 65-68 | initial_speed | float32 | 弹丸初速度 | m/s | - |
| 69-70 | projectile_allowance_17mm | uint16_t | 17mm 弹丸允许发弹量 | - | - |
| 71-72 | projectile_allowance_42mm | uint16_t | 42mm 弹丸允许发弹量 | - | - |
| 73-76 | rfid_status | uint32_t | RFID 卡检测状态 | - | 0-31 位对应不同增益点 ID |

#### RFID 状态详细 ID 映射（对应 Byte 73-76）
0：己方基地增益点
 1：己方中央高地增益点 
 2：对方中央高地增益点 
 3：己方梯形高地增益点 
4：对方梯形高地增益点 
5：己方地形跨越增益点（飞坡）（靠近己方一侧飞坡前） 
6：己方地形跨越增益点（飞坡）（靠近己方一侧飞坡后） 
7：对方地形跨越增益点（飞坡）（靠近对方一侧飞坡前） 
8：对方地形跨越增益点（飞坡）（靠近对方一侧飞坡后） 
9：己方地形跨越增益点（中央高地下方） 
10：己方地形跨越增益点（中央高地上方） 
11：对方地形跨越增益点（中央高地下方） 
12：对方地形跨越增益点（中央高地上方） 
13：己方地形跨越增益点（公路下方） 
14：己方地形跨越增益点（公路上方） 
15：对方地形跨越增益点（公路下方） 
16：对方地形跨越增益点（公路上方） 
17：己方堡垒增益点 
18：己方前哨站增益点 
 19：己方与资源区不重叠的补给区/RMUL 补给区 
20：己方与资源区重叠的补给区 
21：己方装配增益点 
22：对方装配增益点 
23：中心增益点（仅 RMUL 适用） 
24：对方堡垒增益点 
25：对方前哨站增益点
26：己方地形跨越增益点（隧道）（靠近己方一侧公路区下方） 
27：己方地形跨越增益点（隧道）（靠近己方一侧公路区中间） 
28：己方地形跨越增益点（隧道）（靠近己方一侧公路区上方） 
29：己方地形跨越增益点（隧道）（靠近己方梯形高地较低处） 
30：己方地形跨越增益点（隧道）（靠近己方梯形高地较中间） 
31：己方地形跨越增益点（隧道）（靠近己方梯形高地较高处）