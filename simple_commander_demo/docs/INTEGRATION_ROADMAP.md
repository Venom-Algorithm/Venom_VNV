# Simple Commander Integration Roadmap

本文档说明 `simple_commander_demo` 从 demo 到正式集成进 `venom_ws` 的推荐阶段、每个阶段该改什么、为什么这么改。

核心原则：**先稳定任务编排能力，再接真实任务模块，再接真机系统，最后再改名/收编默认入口。** 不建议一开始就把它塞进 `venom_bringup` 或替换旧入口。

## 总体目标

最终推荐形态：

```text
src/venom_vnv/
├── venom_mission_commander/      # 任务编排核心，后续由 simple_commander_demo 演进而来
├── venom_bringup/                # 真机底盘、雷达、定位、Nav2、RViz、mission wrapper launch
└── simulation/venom_nav_simulation/
    └── ...                       # Gazebo、仿真地图、仿真 Nav2/RViz、sim wrapper launch
```

职责边界：

```text
mission commander
→ 读 mission YAML
→ 给 Nav2 发目标点
→ 到点后执行任务插件
→ 记录任务状态

venom_bringup
→ 启动真实机器人硬件链路
→ 启动真实定位/Nav2/RViz
→ 提供真机 mission YAML 和 wrapper launch

simulation
→ 启动 Gazebo/Nav2/RViz
→ 提供仿真地图、world、sim mission wrapper
```

## 阶段 0：Demo 原型阶段

当前阶段基本处于这里。

### 应该做什么

- 保持 `simple_commander_demo` 为独立 ROS2 Python 包。
- 默认使用 mock navigation 和 mock task plugins。
- 保留 `config/simple_mission.yaml` 作为无地图、无硬件的最小演示配置。
- 保留 `docs/TASK_PLUGIN_INTEGRATION_GUIDE.md` 说明插件接入契约。
- 不要修改现有 `venom_bringup` 默认入口。

### 为什么

- 这个阶段目标是验证架构闭环：`YAML → 路点 → 导航接口 → 到点任务 → 状态记录`。
- 独立包能避免影响现有 bringup 和旧 `multi_waypoint_commander`。
- mock-first 能在没有地图、没有真机、没有视觉/机械臂模块时持续验证主流程。

### 不建议做什么

- 不要把代码移动到 `venom_bringup/venom_bringup/`。
- 不要把任务插件直接写死在 `SimpleCommander.run()` 里。
- 不要过早替换现有 launch 默认入口。

## 阶段 1：Docker + Gazebo + Nav2 仿真验证阶段

这一阶段目标是证明 commander 能脱离 mock navigation，通过真实 Nav2 action 控制 Gazebo 里的小车。

### 应该做什么

- 使用 `simple_commander_nav2_sim.launch.py` 启动 commander。
- 使用 `config/rmul_sim_mission.yaml` 验证 RMUL 仿真地图。
- 保持任务插件先用 mock，只验证真实 Nav2 导航链路。
- 在 RViz 里先用 `2D Goal Pose` 单点验证可达，再跑完整 mission。
- 保持 `use_sim_time:=true`。

### 为什么

- 先拆开验证：Nav2 能不能走、任务插件能不能跑，是两类问题。
- 如果 RViz 手动目标都走不通，问题在仿真/Nav2/TF/costmap，不应该先查 commander。
- `use_sim_time:=true` 是 Gazebo 场景必要条件，避免时间源和 TF 时间不一致。

### 主要改动位置

- `launch/simple_commander_nav2_sim.launch.py`
- `config/rmul_sim_mission.yaml`
- `README.md` 中 Docker/RViz/Nav2 运行说明

### 完成标准

- Docker Humble 内能 build `simple_commander_demo`。
- Gazebo/RViz/Nav2 已启动后，commander 能依次发送路点。
- 机器人能在仿真地图里到达每个目标点。
- 到点后 mock 任务能按 YAML 顺序执行。

## 阶段 2：真实任务模块接入阶段

这一阶段目标是把视觉、机械臂、语音、火焰追踪等模块从 mock 替换成真实 service/action/topic 调用。

### 应该做什么

- 继续保留 `SimpleCommander` 主流程不变。
- 优先修改或新增 `task_plugins.py` 里的插件类。
- 按 `docs/TASK_PLUGIN_INTEGRATION_GUIDE.md` 约定接入真实模块。
- 先在 mock navigation 下测真实任务插件，再放到 Nav2/Gazebo 全链路里测。
- 为每个真实插件明确 YAML 参数、blackboard 输入、blackboard 输出、超时策略。

### 为什么

- 任务模块变化频繁，主流程应该稳定。
- 插件边界能把真实 ROS message/service/action 适配逻辑隔离在插件内部。
- 先用 mock navigation 测插件，可以避免“机器人没到点”和“任务接口失败”混在一起排查。

### 主要改动位置

- `simple_commander_demo/task_plugins.py`
- `config/*.yaml` 中对应 task 的参数
- `package.xml` 中新增真实消息/service/action 包依赖
- 必要时新增独立插件文件，例如 `real_task_plugins.py`

### 完成标准

- 每个真实插件都能返回 `TaskExecutionResult`。
- 失败、超时、服务不可用都能返回明确错误。
- `blackboard` key 约定稳定，例如 `detected_item`、`grasped_object`、`meter_reading`。
- 不需要修改 `SimpleCommander.run()` 就能替换 mock/real 实现。

## 阶段 3：真实机器人 bringup 联调阶段

这一阶段目标是让 commander 接入真实底盘、真实雷达、真实定位和真实 Nav2。

### 应该做什么

- 不使用 `simple_commander_nav2_sim.launch.py`，改用通用 launch：`simple_commander_demo.launch.py`。
- 真机运行时使用 `use_nav:=true`、`use_sim_time:=false`。
- 从 `competition_mission_template.yaml` 复制真实 mission 配置，填真实 `map` frame 下的 `x/y/yaw`。
- 在 `venom_bringup` 增加真机 wrapper launch，负责传入真实 mission YAML。
- 保持雷达、底盘、定位、Nav2 参数在真机 bringup 侧维护。

### 为什么

- commander 只应该给 Nav2 发目标，不应该负责启动或维护底层硬件链路。
- 真机时间源必须用系统时间，不能沿用 Gazebo `/clock`。
- 真机地图坐标属于机器人/比赛资产，应放在 `venom_bringup/config/<robot>/missions/`，不应长期放在 commander 核心包里。

### 推荐新增位置

```text
venom_bringup/
├── launch/
│   ├── scout_mini/
│   │   └── scout_mini_mission.launch.py
│   └── sentry/
│       └── sentry_mission.launch.py
└── config/
    ├── scout_mini/
    │   └── missions/
    │       └── competition_mission.yaml
    └── sentry/
        └── missions/
            └── competition_mission.yaml
```

### wrapper launch 应该做什么

wrapper launch 只做参数包装，不写 mission 逻辑：

```text
选择 mission_config
→ 设置 use_nav:=true
→ 设置 use_sim_time:=false
→ 设置 nav2_wait_mode
→ 启动 simple_commander executable
```

### 完成标准

- 真机 Nav2 已经能通过 RViz `2D Goal Pose` 控制底盘。
- commander 能发送同样的 `map` frame 目标点。
- `/cmd_vel` 由 Nav2 发出并能驱动真实底盘。
- 真实任务插件能在对应路点执行。

## 阶段 4：正式包收编阶段

这一阶段目标是把 demo 提升成正式 mission commander 包。

### 应该做什么

- 将 `simple_commander_demo` 改名为正式包名，例如：
  - `venom_mission_commander`
  - `simple_commander`
- 更新 `package.xml`、`setup.py`、Python import 路径、launch package 名。
- 保留独立包结构，不移动进 `venom_bringup/venom_bringup/`。
- 将 demo 配置和正式配置分层：模板留 commander 包，真机配置放 `venom_bringup`。

### 为什么

- `demo` 后缀适合原型，但不适合作为正式比赛/真机入口。
- 独立包边界清晰，方便仿真和真机共同复用。
- 避免 `venom_bringup` 同时承担 bringup 和 mission engine 两种职责。

### 主要改动位置

- 包目录名
- `package.xml` 的 `<name>`
- `setup.py` 的 `package_name` 和 console script
- Python import：`simple_commander_demo.*`
- launch 中 `package='simple_commander_demo'`
- README/docs 中的包名

### 完成标准

- 新包名下 `colcon build --packages-select <new_pkg>` 通过。
- 原有 launch、config、docs 都能通过新包名找到。
- 旧 demo 包名不再出现在正式启动命令中。

## 阶段 5：Docker / CI / 默认构建集成阶段

这一阶段目标是让包进入日常构建和仿真工作流，不再手动 symlink。

### 应该做什么

- 将 commander 包纳入 Docker Humble bootstrap 的 symlink/build 流程。
- 更新 Docker README，不再要求手动：

  ```bash
  ln -sfn /workspaces/venom_vnv/simple_commander_demo /opt/venom_nav_ws/src/simple_commander_demo
  ```

- 如果项目有 CI，把 commander 包加入 build/test 范围。
- 保留 mock mission 作为快速 smoke test。

### 为什么

- 手动 symlink 容易漏，换机器或清 volume 后会重复踩坑。
- 正式包应该和仿真 workspace 一起构建。
- mock smoke test 能快速验证 mission parser、插件注册、主流程没有坏。

### 主要改动位置

- `simulation/venom_nav_simulation/docker/bootstrap_humble_sim.sh`
- `simulation/venom_nav_simulation/AI_DOCKER_WORKFLOW.md`
- `simulation/venom_nav_simulation/README.md`
- 可能的 CI/build 脚本

### 完成标准

- 新容器首次 bootstrap 后自动能 `ros2 launch <commander_pkg> ...`。
- 不需要手动链接 commander 包。
- 修改 Python 源码后通过 `--symlink-install` 能即时生效。

## 阶段 6：替换旧入口阶段

这一阶段目标是把旧的纯 waypoint commander 逐步替换成新的 mission commander。

### 应该做什么

- 先新增新入口，不要直接删除旧入口。
- 在文档中把推荐入口切到 mission commander。
- 保留旧 `multi_waypoint_commander` 一段时间作为 fallback。
- 仿真和真机都 soak 一段时间后，再考虑删除或降级旧入口。

### 为什么

- 旧入口可能仍被其他 launch 或人员使用。
- 新 commander 牵涉任务插件和真实模块，回归面更大。
- 渐进替换能降低比赛前集成风险。

### 完成标准

- 新入口在仿真和真机都稳定。
- 常用文档和 launch 都指向新 commander。
- 旧入口有明确 fallback 或 deprecation 说明。

## 阶段 7：比赛版本强化阶段

这一阶段目标是提高真机比赛可靠性。

### 建议补强内容

- 任务超时和取消：所有插件支持 timeout，后续可接 `cancel()`。
- 持久化恢复：把 `MissionManager.state_data` 保存到文件，支持节点重启后恢复。
- 外部事件中断：接急停、低电量、低血量、通信异常等事件。
- 任务结果日志：保存每个 waypoint/task 的结构化结果。
- 参数化插件 backend：支持 `task_backend:=mock/real`，避免手动改注册顺序。
- 命名空间支持：如果 Nav2 在 namespace 下运行，给 navigator 增加 namespace 参数。

### 为什么

- 比赛环境会有任务失败、定位丢失、硬件超时、急停等异常情况。
- 当前 demo 的状态管理是内存态，适合开发验证，但不够比赛级鲁棒。
- 参数化 backend 能让同一套 mission 在仿真、mock、真机之间切换。

## 远期分支：动态 Mission 生成

如果主线已经完成多轮仿真/真机集成，后续希望进一步泛化到“尽量少手改 waypoint 和 task 绑定”，建议不要直接改造当前主线，而是单独参考 `docs/FUTURE_DYNAMIC_MISSION_BRANCH.md` 里的未来分支设计。

这条分支的核心思想是：

```text
semantic_map + mission_goals + constraints
→ MissionPlanner / MissionCompiler
→ current MissionConfig
→ SimpleCommander
```

也就是说，先提升 mission 的生成方式，而不是先推翻现有执行器。

## 阶段对照表

| 阶段 | 主要目标 | 改 commander 包 | 改 venom_bringup | 改 simulation/Docker | 原因 |
| --- | --- | --- | --- | --- | --- |
| 0 Demo 原型 | 跑通主流程 | 是 | 否 | 否 | 避免影响现有功能 |
| 1 仿真 Nav2 | 验证真实导航 action | 少量 | 否 | 是 | 先证明 Gazebo/Nav2 链路 |
| 2 真实任务 | 接视觉/机械臂/语音 | 是 | 可能加依赖 | 否 | 插件隔离真实模块 |
| 3 真机联调 | 接真实底盘/雷达/Nav2 | 少量参数 | 是 | 否 | 硬件链路属于 bringup |
| 4 正式收编 | 去 demo 化 | 是 | 更新引用 | 更新引用 | 包名和职责正式化 |
| 5 Docker/CI | 默认构建 | 少量 | 否 | 是 | 去掉手动 symlink |
| 6 替换旧入口 | 成为推荐入口 | 否 | 是 | 是 | 渐进替换降低风险 |
| 7 比赛强化 | 提高可靠性 | 是 | 是 | 可能 | 面向异常恢复和稳定性 |

## 最推荐的执行顺序

```text
1. 保持独立 demo 包，继续完善 mock + Nav2 仿真
2. 接真实 task plugins，但不改 SimpleCommander 主流程
3. 在 venom_bringup 增加真机 mission wrapper launch
4. 把真机 mission YAML 移到 venom_bringup/config/<robot>/missions
5. Docker bootstrap 自动包含 commander 包
6. 包名从 simple_commander_demo 升级为 venom_mission_commander
7. 文档和默认入口逐步切到新 commander
8. 补超时、取消、持久化、外部中断等比赛级能力
```

## 判断是否可以进入下一阶段

进入下一阶段前，建议满足这些检查项：

- Demo 阶段完成：mock mission 能稳定跑完。
- 仿真阶段完成：RViz 手动目标和 commander 自动目标都能在 Gazebo 里跑通。
- 真实任务阶段完成：每个插件单独可测，失败时返回明确错误。
- 真机阶段完成：真机 Nav2 本身已稳定，commander 只负责发目标。
- 正式收编阶段完成：包名、launch、docs、Docker 都无旧路径残留。

如果某一阶段不稳定，不建议提前进入后面的“替换旧入口”阶段。
