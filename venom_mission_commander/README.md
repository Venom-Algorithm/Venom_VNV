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

入口、参数、mission YAML schema、实机和 Docker 启动矩阵见 `docs/ENTRYPOINTS_AND_CONFIG.md`。

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
→ 执行固定启动检查，确认配置、插件和导航器状态
→ 按顺序处理每个 waypoint
  → 导航到目标点，或按 skip_navigation 跳过导航
  → 到点后按顺序执行该 waypoint 下的 tasks
  → 每个 task 通过 type 找到对应 TaskPlugin
  → 插件执行后返回 TaskExecutionResult
  → 任务结果写入 MissionManager 和 blackboard
→ 所有 waypoint 完成后 mission 进入 COMPLETED / COMPLETED_WITH_ERRORS / FAILED
```

运行时只有 `MissionCommander` 是真正的 ROS 2 node。`WaypointSpec`、`TaskSpec`、`MissionConfig` 都只是 Python 数据对象，用来承载 YAML 解析后的任务描述。任务插件默认也是普通 Python 对象，但它们可以通过 `TaskContext.node` 借用 `MissionCommander` 去创建 ROS service/action/topic client。

## 模块职责

- `MissionCommander`：总控节点，负责读取参数、加载 mission、创建导航器、注册任务插件，并按路点驱动完整流程。
- `MissionLoader`：把 YAML 里的 `mission`、`waypoints`、`tasks` 解析成 Python 数据结构。
- `WaypointNavigator`：导航适配层；mock 模式只打印并等待，Nav2 模式会把 `WaypointSpec` 转成 `PoseStamped` 后调用 `BasicNavigator.goToPose()`。
- `WaypointTaskRunner`：任务调度器；到达路点后按顺序执行当前路点的 task 列表。
- `MissionStatusReporter`：比赛状态输出器；把当前 waypoint、task、导航尝试和启动检查结果整理成稳定日志。
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

## 启动检查和状态输出

启动检查由 `startup_checks.py` 中的 `StartupChecker` 提供，是固定内建逻辑，不需要在 YAML 里配置。Mission 正式进入 `RUNNING` 前会依次检查：

- `mission_config`：做轻量语义检查，包括 waypoint 数量、重复 waypoint 名和非有限坐标；YAML 结构错误仍由 `MissionLoader` 在加载阶段直接报错。
- `task_plugins_registered`：提前发现 YAML 中写了未注册的 task `type`。
- `navigator_ready`：确认 mock/Nav2 navigator 已完成 ready 阶段；等待时间由 ROS 参数 `navigator_ready_timeout_sec` 控制，默认 30 秒。

运行时会输出 `[STARTUP]`、`[STATUS]`、`[NAV2]` 和 `[SUMMARY]` 日志，方便比赛 2 号机位直接观察当前阶段、waypoint、task、导航尝试次数、最近任务结果和启动检查状态。

默认日志按“比赛可读”优先，不再把底层状态迁移历史直接刷到屏幕。需要排查状态机细节时，可通过 ROS 参数 `log_state_transitions:=true` 重新打开 `MissionManager` 的状态迁移日志。

日志类别、示例格式和相关 ROS 参数见 `docs/ENTRYPOINTS_AND_CONFIG.md` 的“运行日志结构”章节。

## 主要接口

- `MissionCommander.configure()`：读取 YAML、注册任务插件、创建导航器、初始化任务状态。
- `MissionCommander.run()`：执行完整 mission，可根据 YAML 的 `loop` 决定是否循环。
- `MissionCommander.run_startup_checks()`：调用 `StartupChecker`，失败时 mission 不进入运行阶段。
- `StartupChecker.run()`：执行固定启动检查，不依赖 YAML 扩展配置。
- `MissionCommander.run_waypoint()`：处理单个路点，先导航，再执行该路点任务列表。
- `MissionLoader.load(config_path)`：把 YAML 转成 `MissionConfig` / `WaypointSpec` / `TaskSpec`。
- `MissionManager.transition_to()`：记录任务状态切换；默认不直接打印，历史仍保存在 `MissionManager.history`。
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

## 运行、构建与配置

本 README 只保留任务编排包自身的职责说明，不重复维护完整启动命令：

- 入口、参数、mission YAML schema、mock / 本机仿真 / Docker / 真机启动矩阵见 `docs/ENTRYPOINTS_AND_CONFIG.md`。
- 仿真栈、Docker、重建策略和 `competition_10x6` 地图启动流程见 `../simulation/venom_nav_simulation/README.md`。
- Docker bootstrap 行为和镜像/volume 注意事项见 `../simulation/venom_nav_simulation/AI_DOCKER_WORKFLOW.md`。

### 本机源码构建注意

`mission_commander_nav2_sim.launch.py` 只启动 commander node，不会启动 Gazebo、定位、Nav2 或 RViz；运行前必须先由仿真或真机 bringup 启动导航栈。

不通过 Docker 直接构建完整仿真链路时，当前更适合 `Ubuntu 22.04 + ROS 2 Humble` 环境；如果宿主机是 `Ubuntu 24.04 + ROS 2 Jazzy`，建议使用仿真包中的 Humble Docker 工作流。

本机构建命令需要注意：

- `ROS_DISTRO` 应显式匹配目标环境；Humble 仿真链路不要继承已存在的 Jazzy 环境变量。
- `driver/livox_ros_driver2/package.xml` 当前已是 ROS 2 package，一般不需要再用 `package_ROS2.xml` 覆盖。
- `rm_navigation` 的 Nav2 参数依赖 `teb_local_planner::TebLocalPlannerROS`，因此本机构建时也必须保证 TEB 插件和 `teb_msgs` 已进入同一个 workspace。
- Docker 路径下的 TEB / `costmap_converter` overlay、Humble 兼容 patch 和 rosdep 安装策略以 `../simulation/venom_nav_simulation/docker/bootstrap_humble_sim.sh` 为准。

## 后续接真实任务

真实视觉、语音和机械臂接口建议优先替换这些类的内部 mock 方法，而不是改 `MissionCommander` 主流程：

完整任务插件接入规范见 `docs/TASK_PLUGIN_INTEGRATION_GUIDE.md`，里面约定了 YAML task 格式、`BaseTaskPlugin` 接口、`TaskContext` / `TaskExecutionResult` 数据结构、`blackboard` key 和 ROS service/action 接入方式。

`read_meter` 通过 `/perception/read_printed_number` 接入纸上纯数字识别的用法见 `docs/READ_METER_SERVICE_PLUGIN.md`。

如果要规划什么时候接仿真、什么时候接真实任务模块、什么时候纳入 `venom_bringup` 和 Docker 默认构建，见 `docs/INTEGRATION_ROADMAP.md`。

- `DetectItemTaskPlugin`
- `GraspItemTaskPlugin`
- `ReadMeterTaskPlugin`
- `VoiceReportTaskPlugin`
- `DetectFlameTaskPlugin`
- `TrackFlameTaskPlugin`
- `ClassifyPlaceTaskPlugin`

这样主流程仍保持：`导航 → 到点 → 执行任务列表 → 保存状态 → 下一个点`。
