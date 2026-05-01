# piper_mtc_tasks

基于 MoveIt Task Constructor 的 Piper 抓取与放置任务包，用于在仿真中复现当前这套 `pick -> place` 流程。

## 当前能力

- 固定场景下的抓取与放置动作链路
- 基于 MTC 的抓取位姿求解与执行
- Gazebo + MoveIt + Piper 联动仿真
- 配套的验收脚本与 IK 探测工具

当前默认流程已经接通：

1. 打开夹爪
2. 接近目标
3. 求解抓取 IK
4. 闭合夹爪
5. 抬升目标
6. 移动到放置区
7. 打开夹爪
8. 撤离

## 代码位置

- 任务服务端：[src/pick_place_server.cpp](/home/chfyx/venom_ws/src/venom_vnv/manipulation/piper_mtc_tasks/src/pick_place_server.cpp)
- 抓取任务构建：[src/pick_task.cpp](/home/chfyx/venom_ws/src/venom_vnv/manipulation/piper_mtc_tasks/src/pick_task.cpp)
- 放置任务构建：[src/place_task.cpp](/home/chfyx/venom_ws/src/venom_vnv/manipulation/piper_mtc_tasks/src/place_task.cpp)
- 仿真参数：[config/sim_pick_task.yaml](/home/chfyx/venom_ws/src/venom_vnv/manipulation/piper_mtc_tasks/config/sim_pick_task.yaml)
- 启动文件：[launch/sim_pick_task.launch.py](/home/chfyx/venom_ws/src/venom_vnv/manipulation/piper_mtc_tasks/launch/sim_pick_task.launch.py)
- 验收脚本：[scripts/acceptance_pick_place.sh](/home/chfyx/venom_ws/src/venom_vnv/manipulation/piper_mtc_tasks/scripts/acceptance_pick_place.sh)

## 依赖说明

这套流程除了主仓库改动，还依赖两个关键子模块状态：

- `driver/piper_ros`
- `third_party/IFRA_LinkAttacher`

当前仓库的 `.gitmodules` 已经把 `driver/piper_ros` 指到：

- `git@github.com:lzx2530/piper_ros.git`

并且当前效果对应的 `piper_ros` 分支是：

- `venom-manipulation-sync`

如果你是从 fork 拉代码，建议这样初始化：

```bash
cd ~/venom_ws/src
git clone --recurse-submodules git@github.com:lzx2530/Venom_VNV.git venom_vnv
cd venom_vnv
git checkout develop_moveit
git submodule sync --recursive
git submodule update --init --recursive
```

如果 `driver/piper_ros` 没有切到对应分支，可手动执行：

```bash
cd ~/venom_ws/src/venom_vnv/driver/piper_ros
git fetch origin
git switch venom-manipulation-sync
```

## 编译

建议至少编下面这些包：

```bash
cd ~/venom_ws
source /opt/ros/humble/setup.bash
colcon build --packages-select \
  linkattacher_msgs \
  venom_manipulation_interfaces \
  venom_manipulation \
  piper_mtc_tasks
```

编译完成后：

```bash
source ~/venom_ws/install/setup.bash
```

## 启动仿真

带 Gazebo GUI：

```bash
ros2 launch piper_mtc_tasks sim_pick_task.launch.py use_gazebo_gui:=true
```

不带 GUI：

```bash
ros2 launch piper_mtc_tasks sim_pick_task.launch.py use_gazebo_gui:=false
```

如果之前有残留进程，建议先清理：

```bash
pkill -9 -f "gzserver|gzclient|gazebo --verbose|move_group|pick_place_server|spawn_entity.py|robot_state_publisher|joint8_ctrl.py|controller_bringup.py|ros2 launch piper_mtc_tasks"
```

## 发送抓取任务

仿真启动完成后，发送固定场景抓取放置任务：

```bash
ros2 action send_goal /manipulation/execute_task \
  venom_manipulation_interfaces/action/ExecuteTask \
  "{task_type: 1}" --feedback
```

如果返回成功，典型结果会包含：

```text
success: true
stage_reached: 8
message: Pick-and-place MTC task completed.
```

## 验收

仓库里提供了一个验收脚本：

```bash
bash manipulation/piper_mtc_tasks/scripts/acceptance_pick_place.sh
```

如果你更关心可视化效果，建议直接看 Gazebo GUI，并配合上面的 action 命令做一次人工确认。

## 当前实现特点

- 当前抓取目标来自固定场景参数，不是视觉输入
- MTC 会根据目标位姿自动解抓取 IK
- 当前成功抓取主要依赖 Gazebo 接触/摩擦，不是强制附着
- `sim_pick_task.yaml` 中当前默认：

```yaml
enable_gazebo_attachment: false
```

也就是说，当前这版更接近“夹住了再搬运”，而不是“吸附后搬运”。

## 后续接视觉时怎么改

现阶段主链路已经具备：

- 给目标
- 自动解抓取
- 执行动作

所以以后接视觉，核心不是重写 MTC，而是把“固定目标来源”换成“视觉输出目标”。

最关键的输入会是：

- 目标在规划坐标系下的位置
- 目标朝向
- 目标尺寸或可抓取边界
- 目标置信度

## 已知边界

- 当前主仓库之外，`driver/piper_ros` 的分支状态也会直接影响效果
- 如果子模块没有同步到正确提交，可能出现“代码在、效果不在”的情况
- 这套流程现在适合固定场景调通，不等于已经完成视觉接入

## 建议

如果你接下来继续推进，推荐顺序是：

1. 先固定当前这套仿真复现方法
2. 再接入视觉目标来源
3. 最后再做多轮稳定性验收
