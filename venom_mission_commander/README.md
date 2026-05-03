# venom_mission_commander

`venom_mission_commander` 是一个独立 ROS 2 Python 任务编排包，用来验证“按路点顺序导航，到点后执行任务，再去下一个点”的任务编排流程。

默认运行模式是 mock：不需要真实地图、Nav2 action server、视觉节点、语音节点或机械臂节点，只打印流程并在内存 `blackboard` 中传递模拟结果。

## 示例任务路线

```text
起停区
→ 任务点一：识别物品 → 机械臂夹取
→ 任务点二：识别电表图像 → 语音播报
→ 任务点三：识别火焰图片 → 追踪
→ 任务点四：物品分类 → 放置
→ 回到起停区
```

默认 mock 坐标写在 `config/simple_mission.yaml` 中。接真实仿真导航时优先使用 `config/rmul_sim_mission.yaml`；后续接比赛地图时复制 `config/competition_mission_template.yaml` 后替换 `x/y/yaw`。

从原型演进到正式工程集成的阶段路线见 `docs/INTEGRATION_ROADMAP.md`。

如果未来想把 mission 输入进一步泛化为“语义地图 + 任务目标 + 约束”，并动态生成 waypoint/task 绑定，可参考 `docs/FUTURE_DYNAMIC_MISSION_BRANCH.md`。

## 工作流程概览

`venom_mission_commander` 的主流程可以理解成一条固定执行链：

```text
launch / ros2 run
→ 启动 MissionCommander 这个 ROS 2 node
→ 读取 mission YAML
→ 解析成 MissionConfig / WaypointSpec / TaskSpec
→ 初始化导航器和任务插件
→ 按顺序处理每个 waypoint
  → 导航到目标点，或按 skip_navigation 跳过导航
  → 到点后按顺序执行该 waypoint 下的 tasks
  → 每个 task 通过 type 找到对应 TaskPlugin
  → 插件执行后返回 TaskExecutionResult
  → 任务结果写入 MissionManager 和 blackboard
→ 所有 waypoint 完成后 mission 进入 COMPLETED / FAILED
```

运行时只有 `MissionCommander` 是真正的 ROS 2 node。`WaypointSpec`、`TaskSpec`、`MissionConfig` 都只是 Python 数据对象，用来承载 YAML 解析后的任务描述。任务插件默认也是普通 Python 对象，但它们可以通过 `TaskContext.node` 借用 `MissionCommander` 去创建 ROS service/action/topic client。

## 模块职责

- `MissionCommander`：总控节点，负责读取参数、加载 mission、创建导航器、注册任务插件，并按路点驱动完整流程。
- `MissionLoader`：把 YAML 里的 `mission`、`waypoints`、`tasks` 解析成 Python 数据结构。
- `WaypointNavigator`：导航适配层；mock 模式只打印并等待，Nav2 模式会把 `WaypointSpec` 转成 `PoseStamped` 后调用 `BasicNavigator.goToPose()`。
- `WaypointTaskRunner`：任务调度器；到达路点后按顺序执行当前路点的 task 列表。
- `TaskPluginRegistry`：任务插件表；根据 YAML 里的 `type` 找到对应插件。
- `BaseTaskPlugin`：任务插件统一接口；后续接真实视觉、机械臂、语音时主要扩展这里。
- `MissionManager`：轻量任务状态机和状态记录器；记录当前路点、当前任务、最近结果、失败原因和状态切换历史。

## 数据流和插件协作

一个 task 的输入主要来自两处：

- YAML 参数：除 `name` 和 `type` 外的字段都会进入 `TaskSpec.params`，例如 `target`、`source`、`timeout_sec`、`place_zone`。
- `blackboard`：任务之间共享的运行时数据，例如识别结果、夹取结果、电表读数。

插件执行后也有两类输出：

- `TaskExecutionResult`：告诉 `WaypointTaskRunner` 当前任务是否成功、日志消息是什么、结果数据是什么。
- `context.blackboard`：把结果留给后续任务使用，例如 `detect_item` 写入 `detected_item`，`grasp_item` 再读取它。

典型任务链如下：

```text
detect_item
→ 写 blackboard["detected_item"]

grasp_item
→ 读 blackboard["detected_item"]
→ 写 blackboard["grasped_object"]

classify_place
→ 读 blackboard["grasped_object"]
→ 写 blackboard["last_placement"]
```

`MissionManager` 不直接执行任务，它只记录状态。任务开始时 `WaypointTaskRunner` 会调用 `mark_task_started()`，任务失败时调用 `mark_task_failed()`，如果配置了 `stop_on_task_failure: true`，则进一步调用 `fail()` 把 mission 切到 `FAILED`。

## 主要接口

- `MissionCommander.configure()`：读取 YAML、注册任务插件、创建导航器、初始化任务状态。
- `MissionCommander.run()`：执行完整 mission，可根据 YAML 的 `loop` 决定是否循环。
- `MissionCommander.run_waypoint()`：处理单个路点，先导航，再执行该路点任务列表。
- `MissionLoader.load(config_path)`：把 YAML 转成 `MissionConfig` / `WaypointSpec` / `TaskSpec`。
- `MissionManager.transition_to()`：记录任务状态切换。
- `MissionManager.save_state()`：保存当前路点、当前任务、最近任务结果等运行状态。
- `MockWaypointNavigator`：默认导航器，不依赖 Nav2。
- `Nav2WaypointNavigator`：真实 Nav2 导航器，使用 `nav2_simple_commander.BasicNavigator.goToPose()`。
- `WaypointTaskRunner.run_tasks()`：按顺序执行当前路点的 tasks。
- `TaskPluginRegistry.get(task_type)`：根据 YAML 的 `type` 找到任务插件。
- `BaseTaskPlugin.execute(context, spec)`：任务插件统一入口。

## 当前 mock 任务插件

- `detect_item`：模拟识别物品，写入 `blackboard["detected_item"]`。
- `grasp_item`：模拟机械臂夹取，读取 `detected_item`，写入 `blackboard["grasped_object"]`。
- `read_meter`：模拟电表图像识别，写入 `blackboard["meter_reading"]`。
- `voice_report`：模拟语音播报，默认读取 `meter_reading`。
- `detect_flame`：模拟火焰图片识别，写入 `blackboard["flame_detection"]`。
- `track_flame`：模拟火焰追踪，读取 `flame_detection`。
- `classify_place`：模拟分类放置，读取 `grasped_object`。
- `wait`：模拟等待。

## 本机工作区运行

```bash
cd /home/alex/venom_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install --packages-select venom_mission_commander
source install/setup.bash
ros2 launch venom_mission_commander mission_commander.launch.py use_nav:=false
```

也可以直接指定配置：

```bash
ros2 run venom_mission_commander mission_commander \
  --ros-args \
  -p mission_config:=/home/alex/venom_ws/src/venom_vnv/venom_mission_commander/config/simple_mission.yaml \
  -p use_nav:=false
```

## Docker 里运行 mock 示例

当前 Humble Docker 的仓库挂载点是 `/workspaces/venom_vnv`，仿真工作区是 `/opt/venom_nav_ws`。这个任务编排包没有修改 bootstrap 脚本，所以首次在容器内运行时手动把包 symlink 进仿真工作区即可。

```bash
cd /workspaces/venom_vnv/simulation/venom_nav_simulation
./docker/run_humble_sim.sh
```

进入容器后：

```bash
source /opt/ros/humble/setup.bash
mkdir -p /opt/venom_nav_ws/src
ln -sfn /workspaces/venom_vnv/venom_mission_commander /opt/venom_nav_ws/src/venom_mission_commander
cd /opt/venom_nav_ws
colcon build --symlink-install --packages-select venom_mission_commander
source install/setup.bash
ros2 launch venom_mission_commander mission_commander.launch.py use_nav:=false
```

## Docker 里接 Gazebo / Nav2 / RViz

第一步先启动现有 Humble 仿真导航栈。这个 launch 负责 Gazebo、定位、Nav2 和 RViz；`venom_mission_commander` 只作为 Nav2 action client，不重复启动导航栈。

终端 1：进入容器并启动仿真导航。

```bash
cd /workspaces/venom_vnv/simulation/venom_nav_simulation
source /opt/ros/humble/setup.bash
source /opt/venom_nav_ws/install/setup.bash
ros2 launch rm_nav_bringup bringup_sim.launch.py \
  world:=RMUL \
  mode:=nav \
  lio:=pointlio \
  localization:=slam_toolbox \
  lio_rviz:=False \
  nav_rviz:=True
```

第二步先在 RViz 里手动用 `2D Goal Pose` 验证机器人能导航。如果手动目标都失败，先排查地图、定位、costmap、TF 和 Nav2 lifecycle，不要先查 commander。

终端 2：启动真实 Nav2 模式的 commander。

```bash
source /opt/ros/humble/setup.bash
source /opt/venom_nav_ws/install/setup.bash
ros2 launch venom_mission_commander mission_commander_nav2_sim.launch.py
```

等价的显式命令是：

```bash
ros2 launch venom_mission_commander mission_commander.launch.py \
  use_nav:=true \
  use_sim_time:=true \
  nav2_wait_mode:=bt_navigator \
  mission_config:=/opt/venom_nav_ws/src/venom_mission_commander/config/rmul_sim_mission.yaml
```

`mission_commander_nav2_sim.launch.py` 默认使用 `config/rmul_sim_mission.yaml`、`use_nav:=true`、`use_sim_time:=true`，适合在 Gazebo/RViz/Nav2 已经启动后直接验证整条链路。

## 接真实 Nav2

启动仿真导航栈后，把 `use_nav` 改成 `true`：

```bash
ros2 launch venom_mission_commander mission_commander.launch.py \
  use_nav:=true \
  use_sim_time:=true \
  nav2_wait_mode:=bt_navigator
```

如果后续改成 AMCL 等完整 Nav2 lifecycle 流程，可以尝试：

```bash
ros2 launch venom_mission_commander mission_commander.launch.py use_nav:=true nav2_wait_mode:=full
```

## 后续接比赛地图

建议保持“任务插件不变，只换地图坐标”的接入方式：

1. 复制模板：

   ```bash
   cp /opt/venom_nav_ws/src/venom_mission_commander/config/competition_mission_template.yaml \
      /opt/venom_nav_ws/src/venom_mission_commander/config/my_competition_mission.yaml
   ```

2. 启动目标地图对应的 Gazebo/Nav2/RViz。
3. 在 RViz 里逐个验证可达点，记录 `map` frame 下的 `x/y/yaw`。
4. 只替换 `my_competition_mission.yaml` 中的坐标和地图说明，尽量保持路点名与任务名稳定。
5. 用同一个 launch 跑新地图任务：

   ```bash
   ros2 launch venom_mission_commander mission_commander.launch.py \
     use_nav:=true \
     use_sim_time:=true \
     nav2_wait_mode:=bt_navigator \
     mission_config:=/opt/venom_nav_ws/src/venom_mission_commander/config/my_competition_mission.yaml
   ```

比赛地图接入时优先检查这些条件：

- 所有 waypoint 都使用 `frame_id: map`，并且地图 origin 与 RViz 显示一致。
- 每个任务点先用 RViz `2D Goal Pose` 单独验证可达，再跑完整 mission。
- 起停区如果需要真实返航，`return_start_area` 必须填真实起点坐标；不要只依赖 `start_area.skip_navigation`。
- 如果切换 AMCL 或完整 lifecycle 流程，再尝试 `nav2_wait_mode:=full`。

## 后续接真实任务

真实视觉、语音和机械臂接口建议优先替换这些类的内部 mock 方法，而不是改 `MissionCommander` 主流程：

完整任务插件接入规范见 `docs/TASK_PLUGIN_INTEGRATION_GUIDE.md`，里面约定了 YAML task 格式、`BaseTaskPlugin` 接口、`TaskContext` / `TaskExecutionResult` 数据结构、`blackboard` key 和 ROS service/action 接入方式。

如果要规划什么时候接仿真、什么时候接真实任务模块、什么时候纳入 `venom_bringup` 和 Docker 默认构建，见 `docs/INTEGRATION_ROADMAP.md`。

- `DetectItemTaskPlugin`
- `GraspItemTaskPlugin`
- `ReadMeterTaskPlugin`
- `VoiceReportTaskPlugin`
- `DetectFlameTaskPlugin`
- `TrackFlameTaskPlugin`
- `ClassifyPlaceTaskPlugin`

这样主流程仍保持：`导航 → 到点 → 执行任务列表 → 保存状态 → 下一个点`。
