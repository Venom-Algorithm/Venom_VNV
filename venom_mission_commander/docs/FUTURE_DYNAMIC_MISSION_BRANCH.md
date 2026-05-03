# Future Dynamic Mission Branch

本文档描述 `venom_mission_commander` 的一个**远期发展分支**：当现有“固定 mission YAML + 顺序执行”的方案已经稳定落地，并完成多轮仿真/真机集成后，可以考虑引入一套更泛化的“动态 mission 生成”方案。

这不是当前主线的立即实现目标，而是给后续几代迭代预留的一条清晰演进路径。

## 1. 为什么要单独保留这一条分支

当前主线方案的优点是：

- 简单直接，容易联调。
- 对 Nav2、Gazebo、真机 bringup 的耦合较低。
- 对比赛任务来说，可控性强，行为容易复现。
- 当前 `MissionCommander` 主流程已经围绕“固定路点 + 固定任务列表”建立起来。

但它也有明显局限：

- 地图一变，通常要手动改 waypoint 坐标。
- 任务要求一变，通常要手动改任务列表。
- 路点和任务的对应关系是人工写死的。
- 如果同一类比赛每年地图不同、任务点布局不同，复用成本会逐渐升高。

因此，长期来看值得探索一种更泛化的方式：

```text
不再直接手写“路点 -> 任务”
而是先描述“地图语义 + 比赛目标 + 约束条件”
再自动生成当前执行器要跑的 mission
```

## 2. 这条分支的定位

这条分支不是要替换当前执行主流程，而是要在当前执行器前面加一层：

```text
高层任务描述
→ 动态 mission 规划/编译
→ 生成标准 MissionConfig
→ 交给现有 MissionCommander 执行
```

也就是说：

- **主线执行器继续保留**。
- **动态方案先作为前置编译层存在**。
- **输出仍尽量兼容当前 `MissionLoader` / `MissionConfig`**。

这样做的原因是：

- 当前 `MissionCommander` 主循环已经具备可复用价值。
- 真正变化大的，是“输入如何表达”，而不是“怎么顺序执行”。
- 先稳定后端执行，再升级前端 mission 生成，比直接重写整个系统风险更低。

## 3. 总体设计目标

远期泛化方案建议做到以下三点：

### 3.1 任务目标不再直接绑定固定路点

从：

```yaml
waypoints:
  - name: task_point_2_meter_voice
    x: 2.6
    y: 1.8
    tasks:
      - type: read_meter
      - type: voice_report
```

演进到：

```yaml
goals:
  - id: report_meter
    type: read_and_report_meter
    site_kind: meter_station
```

也就是用户表达“要完成什么”，而不是“去第几个点做什么”。

### 3.2 地图从“坐标集合”升级为“语义地图”

从：

```text
只有 x / y / yaw
```

演进到：

```text
站点 ID
+ 站点类型
+ 候选 approach pose
+ 推荐朝向
+ 观察位/操作位
+ 可操作半径
+ 禁行约束
```

也就是不仅知道“这个点在哪里”，还知道“这个点是做什么的”。

### 3.3 任务插件从“执行接口”升级为“能力接口”

现在插件只表达：

```text
这个 task_type 怎么执行
```

未来建议插件还表达：

```text
它能做什么
需要什么输入
产出什么结果
适用于哪些语义站点
是否需要机械臂/视觉/语音等资源
```

这样规划器才能自动决定：

- 哪个任务该放在哪个语义点执行。
- 哪个插件链能满足当前目标。
- 前后任务的数据依赖是否成立。

## 4. 推荐架构

建议在现有执行器前面增加一层规划/编译系统：

```text
MissionCommander
├── MissionPlanner
│   ├── SemanticMapLoader
│   ├── MissionGoalLoader
│   ├── CapabilityRegistry
│   ├── BindingResolver
│   ├── ConstraintChecker
│   ├── ReachabilityChecker
│   └── MissionCompiler
├── MissionManager
├── WaypointNavigator
├── WaypointTaskRunner
└── TaskPluginRegistry
```

### 4.1 `SemanticMapLoader`

负责读取语义地图，而不是纯路点配置。

它的职责是：

- 读取语义站点定义。
- 读取候选导航位姿和操作位姿。
- 读取区域类型、对象类型、禁行区等静态信息。

### 4.2 `MissionGoalLoader`

负责读取比赛要求或本场任务目标。

例如：

- 去某类区域抓取某类物体。
- 读取某类设备的状态并播报。
- 在火焰区域完成检测和追踪。
- 完成后必须返航。

### 4.3 `CapabilityRegistry`

这是未来对 `TaskPluginRegistry` 的升级。

它不只存：

- `task_type -> plugin`

还要存：

- 插件能力名。
- 支持的目标类型。
- 需要的输入 key。
- 输出的 blackboard key。
- 依赖的硬件或资源。
- 默认超时、执行代价、优先级。

### 4.4 `BindingResolver`

这是最关键的一层。

它负责把：

```text
任务目标
```

绑定为：

```text
某个语义站点 + 某组 task plugins + 某个执行顺序
```

例如：

```text
目标：read_and_report_meter
→ 候选站点：所有 kind=meter_station 的 site
→ 候选任务链：read_meter -> voice_report
→ 输出：一个具体 waypoint + 两个具体 task
```

### 4.5 `ConstraintChecker`

负责做运行前静态校验，避免生成一条一开始就不合理的 mission。

它至少应检查：

- 任务依赖是否满足。
- 插件输入输出链是否闭合。
- 必需的语义站点是否存在。
- 是否存在不可执行目标。
- 是否满足返航或顺序约束。

### 4.6 `ReachabilityChecker`

负责在 mission 编译前，对候选点做可达性评估。

推荐优先做：

- 静态几何规则检查。
- Gazebo/RViz 手工验证。
- 后续再接 Nav2 planner 做自动 path feasibility 检查。

### 4.7 `MissionCompiler`

负责把高层描述编译回当前执行器能直接消费的 `MissionConfig`。

这一步非常重要，因为它决定了远期方案能否与当前主线共存。

推荐原则：

- 输出结构尽量保持兼容当前 `MissionLoader`。
- 不要一上来就改掉 `MissionCommander.run()` 的整体执行方式。

## 5. 输入格式的建议演进

建议不要把所有信息都塞进一个超级 YAML，而是分层管理。

### 5.1 `semantic_map.yaml`

表达地图语义和候选站点。

示例概念：

```yaml
map:
  name: competition_map
  frame_id: map

sites:
  - id: start_area
    kind: start_zone
    poses:
      - x: 0.0
        y: 0.0
        yaw: 0.0

  - id: pickup_zone_a
    kind: pickup_zone
    poses:
      - x: 1.2
        y: 0.8
        yaw: 0.0

  - id: meter_station_1
    kind: meter_station
    poses:
      - x: 2.6
        y: 1.8
        yaw: 1.57
```

### 5.2 `mission_goals.yaml`

表达本场比赛要求完成什么。

示例概念：

```yaml
goals:
  - id: pick_object_goal
    type: pick_object
    object_class: example_object
    from_site_kind: pickup_zone

  - id: report_meter_goal
    type: read_and_report_meter
    site_kind: meter_station

  - id: track_fire_goal
    type: detect_and_track_flame
    site_kind: fire_zone

  - id: place_object_goal
    type: classify_and_place
    target_site_kind: place_zone
```

### 5.3 `constraints.yaml`

表达顺序、依赖、策略和边界条件。

例如：

- 哪些任务必须按顺序执行。
- 哪些任务允许跳过。
- 最后是否必须返航。
- 总时间不足时优先做哪些高价值目标。

### 5.4 `robot_profile.yaml`

表达机器人平台相关的能力和限制。

例如：

- 机械臂工作距离。
- 相机推荐观察距离。
- 最小转弯空间。
- 插件使用的真实接口配置。

### 5.5 `compiled_mission.yaml`

这是动态分支的最终产物，仍旧输出成当前执行器能跑的结构：

```yaml
mission:
  id: auto_generated_mission

waypoints:
  - name: pickup_zone_a_pick_object
    x: 1.2
    y: 0.8
    yaw: 0.0
    tasks:
      - type: detect_item
      - type: grasp_item
```

这样动态层和执行层之间边界清晰，不会强迫整个工程同时重构。

## 6. 运行时逻辑建议

推荐采用：

```text
启动时动态生成
+ 运行中有限回退
```

而不是：

```text
运行中全局无限制重规划
```

### 6.1 启动时动态生成

建议流程：

```text
读取 semantic_map
→ 读取 mission_goals
→ 读取 constraints
→ 读取 capability 信息
→ 选择候选站点
→ 选择任务链
→ 检查依赖与可达性
→ 排序并生成 compiled mission
→ 交给现有 MissionCommander 执行
```

### 6.2 运行中有限回退

建议只做这类受约束的回退：

- 当前观察位失败，换同站点备用 pose。
- 当前语义点不可达，换同类候选站点。
- 当前插件失败，切换到兼容的备用实现。

不建议早期就做：

- 全部任务实时重新排序。
- 根据开放世界感知结果自动新增任务。
- 无边界的全局规划搜索。

原因是这些能力虽然“更智能”，但调试代价、比赛风险和解释成本都会显著上升。

## 7. 这条分支里哪些内容仍然必须人工维护

即使进入远期动态方案，下面这些资产仍然不适合完全自动化：

### 7.1 地图坐标和语义点校准

- 起点、返航点。
- 电表观察位。
- 夹取操作位。
- 放置操作位。
- 狭窄区、禁行区、安全距离。

原因：这些内容直接依赖真实地图、视角、底盘尺寸和机械臂工作空间。

### 7.2 真实设备接口

- 视觉 service/action。
- 机械臂 action。
- 语音播报接口。
- 火焰检测和追踪接口。

原因：接口协议、超时、错误码和 topic/service/action 名都高度平台相关。

### 7.3 能力元数据

- 哪个插件适合哪类目标。
- 插件需要什么输入。
- 插件输出什么结果。
- 哪些目标必须先做。

原因：这些知识是业务定义，不应该由系统猜测。

### 7.4 比赛策略

- 哪些任务优先级更高。
- 某任务失败后跳过还是重试。
- 何时返航保底。
- 截止时间前如何保分。

原因：这些属于策略层，而不是纯技术自动化问题。

## 8. 为什么不建议现在就全面切过去

这条分支虽然值得保留，但不建议当前就转主线，原因很明确：

- 当前主线刚从原型走向仿真/真机集成，优先级应是稳定执行链路。
- 当前插件体系仍以 mock-first 为主，真实接口和失败语义还在逐步补齐。
- 当前 `MissionManager` 仍是内存态，尚未完全具备比赛级恢复能力。
- 如果同时推进“真机联调”和“动态规划架构”，风险会叠加。

所以更合理的策略是：

```text
主线先走稳定落地
未来分支先保留设计文档
等主线成熟后，再逐阶段抽象到动态方案
```

## 9. 推荐落地顺序

如果未来要真的启动这条分支，建议顺序如下：

### 第 1 步：先做 MissionCompiler

- 输入高层配置。
- 输出当前 `MissionConfig`。
- 不动主执行器。

这是成本最低、收益最高的一步。

### 第 2 步：引入语义地图

- 把硬编码 waypoint 升级为语义站点。
- 为站点支持多个候选 pose。

这样换地图时不用重写整个任务链。

### 第 3 步：给插件补能力声明

- 从“能执行什么 task_type”
- 升级到“能满足什么 goal、需要什么输入、输出什么结果”

这样规划器才有依据做自动绑定。

### 第 4 步：加入约束检查和可达性检查

- 先在 mission 生成阶段发现问题。
- 不要把明显错误的配置放到执行期才报错。

### 第 5 步：加入有限回退

- 只处理备用点、备用姿态、备用插件。
- 先不要全局重规划。

### 第 6 步：比赛级强化

- deadline-aware 策略。
- 持久化恢复。
- 外部中断。
- 降级策略。

## 10. 与现有文档的关系

这份文档和现有文档的关系建议理解为：

- `docs/TASK_PLUGIN_INTEGRATION_GUIDE.md`
  - 说明当前主线下，任务插件如何接入。
- `docs/INTEGRATION_ROADMAP.md`
  - 说明当前主线如何从原型走向仿真、真机和正式集成。
- `docs/FUTURE_DYNAMIC_MISSION_BRANCH.md`
  - 说明在主线成熟后，如何进一步演进到更泛化的动态 mission 生成方案。

也就是说，这份文档不是当前主线开发 checklist，而是**未来架构分支设计说明**。

## 11. 最终建议

一句话总结：

```text
不要现在就推翻“固定 mission + 稳定执行器”主线，
而是把“动态 mission 生成”作为未来分支，
先以 MissionCompiler 的形式接入，
让输入越来越抽象，让执行后端尽量保持稳定。
```

如果未来确实要启动这一分支，推荐第一个落地点不是“在线智能规划”，而是：

```text
semantic_map + mission_goals + constraints
→ compile
→ current MissionConfig
```

这会是风险最低、最符合当前工程演进节奏的切入点。
