---
title: 开发说明
description: 面向多人协作开发的环境基线、常用软件、Git 流程、子模块协作与调试建议。
---

## 适用对象

本页主要面向以下情况：

- 团队成员较多，需要统一开发环境和协作流程
- 需要同时维护主仓库、子模块和文档站点
- 需要在 Ubuntu + ROS 2 Humble 环境下长期开发和调试
- 需要通过 fork / Pull Request 的方式参与协作

如果你只是第一次部署本项目，优先阅读：

- [快速开始](../home/quick_start.md)
- [环境准备](../deployment/environment.md)
- [雷达配置](../deployment/lidar_setup.md)

## 推荐开发机基线

| 项目 | 推荐基线 | 说明 |
| --- | --- | --- |
| 操作系统 | Ubuntu 22.04 LTS | 当前仓库默认按该版本维护 |
| ROS 版本 | ROS 2 Humble | 当前主工作区统一基线 |
| Python | Python 3.10 | Ubuntu 22.04 默认版本 |
| 构建工具 | `colcon`、`rosdep` | ROS 2 工作区基础工具 |
| 编译工具链 | GCC / G++ 11、CMake | 直接使用 Ubuntu 22.04 默认工具链即可 |
| 版本管理 | Git + GitHub | 用于 fork、分支、PR 和子模块管理 |
| 编辑器 | VS Code | 推荐作为统一编辑器 |
| AI 助手 | Codex | 可用于代码阅读、文档整理和小规模改动辅助 |
| 文档预览 | Docker | 推荐用容器预览 GitHub Pages 文档 |

## 按模块补充安装的依赖

并不是所有同学都需要安装所有依赖，可以按任务方向补齐：

- Mid360 / Point-LIO / Fast-LIO 方向：
  - `Livox-SDK2`
  - 参考 [雷达配置](../deployment/lidar_setup.md)
- RealSense D435i 方向：
  - `librealsense2`
  - 参考 [RealSense 配置](../deployment/realsense_setup.md)
- 底盘方向：
  - `can-utils`
  - 对应底盘驱动与 SDK
  - 参考 [底盘 CAN 部署](../deployment/chassis_can_setup.md)
- 机械臂方向：
  - Piper 机械臂相关 CAN 环境
  - 参考 [机械臂 CAN 部署](../deployment/piper_can_setup.md)
- PX4 / 无人机方向：
  - PX4、Micro XRCE-DDS Agent、桥接相关依赖
- 文档维护方向：
  - Docker
  - Markdown 编辑环境
- 仿真方向：
  - Gazebo / 仿真相关工作区依赖

## 推荐工作区结构

统一建议使用以下目录结构：

```text
~/venom_ws/
├── src/
│   └── venom_vnv/
└── build/ install/ log/
```

主仓库建议放在：

```bash
~/venom_ws/src/venom_vnv
```

每次打开新终端后，先确认环境：

```bash
source /opt/ros/humble/setup.bash
source ~/venom_ws/install/setup.bash
```

如果工作区还没编译过，第二条命令可以暂时不执行。

## VS Code 使用建议

VS Code 建议作为统一编辑器，原因是：

- 搜索项目内话题、TF、参数、launch 文件比较方便
- Python、C++、YAML、Markdown 都能统一处理
- 终端、Diff、Git 历史和插件生态较完整

建议优先安装以下类型的扩展：

- C / C++
- Python
- CMake
- YAML
- Markdown
- Git 增强类扩展
- ROS 辅助类扩展

日常使用建议：

- 直接用仓库根目录作为 VS Code workspace
- 优先使用全局搜索检查话题名、TF、参数是否统一
- 提交前先在 VS Code 或 `git diff` 中检查改动
- 不要编辑 `build/`、`install/`、`log/` 下的生成文件
- 修改 launch、yaml、文档时，尽量同步检查对应模块页是否需要更新

## Codex 使用建议

如果你使用 Codex 辅助开发，建议遵守以下规则：

- Codex 只在你自己的 fork 和分支里工作
- 适合让 Codex 处理：
  - 文档整理
  - 配置项说明补全
  - launch / yaml / markdown 的结构性调整
  - 大量重命名或接口一致性检查
  - 阅读某个模块并总结输入输出关系
- 不要让 Codex 在你没看过 diff 的情况下直接提交或推送
- 涉及以下内容时必须人工复核：
  - 远端地址修改
  - 子模块提交指针更新
  - 删除文件或大范围重构
  - 话题、TF、frame_id、接口协议变更
- Codex 改完后，至少自己再做一次：
  - `git diff`
  - 目标包编译或最小范围验证
  - 对照文档检查命令是否可复现

## GitHub 协作模型

在仓库正式开放写权限之前，统一采用：

```text
fork -> clone -> branch -> commit -> push -> Pull Request -> review -> merge
```

这条流程至少完整走通一次之后，再考虑开放主仓库写权限。

### 第一步：先 fork

每位同学先在 GitHub 上 fork 官方仓库：

- 官方仓库：`Venom-Algorithm/Venom_VNV`
- 个人仓库：`<your-name>/Venom_VNV`

### 第二步：克隆你自己的 fork

推荐拉你自己的 fork，而不是直接拉组织仓库：

```bash
cd ~
mkdir -p ~/venom_ws/src
git clone --recurse-submodules https://github.com/<your-name>/Venom_VNV.git ~/venom_ws/src/venom_vnv
cd ~/venom_ws/src/venom_vnv
git remote add upstream https://github.com/Venom-Algorithm/Venom_VNV.git
git remote -v
```

此时推荐约定：

- `origin` 指向你自己的 fork
- `upstream` 指向组织仓库

如果你需要方便 push，也可以把自己 fork 的 `pushurl` 改成 SSH。

### 第三步：同步上游

开始新任务前，先同步上游最新版本：

```bash
cd ~/venom_ws/src/venom_vnv
git fetch upstream
git checkout master
git merge --ff-only upstream/master
git push origin master
git submodule sync --recursive
git submodule update --init --recursive
```

### 第四步：新建分支，不要直接改 `master`

```bash
cd ~/venom_ws/src/venom_vnv
git checkout -b feat/<short-topic>
```

推荐分支命名：

- `feat/<topic>`
- `fix/<topic>`
- `docs/<topic>`
- `refactor/<topic>`

## 任务管理建议

当并行开发人数较多时，建议不要只靠口头同步，最好配合 GitHub Issues 或 GitHub Projects 统一管理。

建议每个任务至少写清楚：

| 字段 | 建议内容 |
| --- | --- |
| 任务标题 | 尽量直接写模块名或目标，例如 `PX4 bridge 联调`、`Ego-planner 接入` |
| 负责同学 | 至少一位主负责人 |
| 所属模块 | `driver`、`perception`、`localization`、`planning`、`system`、`simulation` 之一 |
| 依赖关系 | 例如“依赖 Mid360 链路先打通” |
| 代码位置 | 主仓库还是某个子模块 |
| 交付物 | 代码、文档、launch、参数、演示视频、采购清单等 |
| 验证方式 | 至少给出一条可复现命令或验证步骤 |

建议 Project 看板至少分成：

- `Todo`
- `In Progress`
- `Blocked`
- `Review`
- `Done`

像下面这类方向都建议单独拆成 issue，而不是揉在一个大任务里：

- 机体与硬件集成
- Ego-planner / TEB / MoveIt 一类规划与运动模块
- RTK、Mid360、Point-LIO、Fast-LIO 一类定位链路
- PX4 bridge、DDS Agent、Simple Commander 一类飞控链路
- YOLO、二维码识别、自瞄、抛投感知一类感知链路
- Gazebo、Isaac Sim、`venom_nav_simulation` 一类仿真链路

这样做的目的不是形式化，而是避免二十个人同时改仓库时，没人知道某个模块现在到底归谁维护。

## 子模块协作规则

这个仓库包含多个子模块，所以需要特别注意。

### 按需拉取子模块

如果只开发某一类功能，不需要每次都递归拉取全部子模块。主仓库提供了 Makefile profile：

| 命令 | 适用场景 |
| --- | --- |
| `make submodules-ugv` | 无人车真机：底盘、机械臂、雷达、相机、串口、定位、YOLO |
| `make submodules-sim` | 纯仿真：`venom_nav_simulation` 与 `ego-planner-swarm` |
| `make submodules-ugv-sim` | 无人车仿真：仿真、Point-LIO、Ego Planner、YOLO |
| `make submodules-auto-aim` | 自瞄开发：`rm_auto_aim`、海康相机、串口 |
| `make submodules-uav` | 无人机开发：PX4 bridge 与 Ego Planner |
| `make submodules-all` | 全量拉取所有子模块 |

示例：

```bash
cd ~/venom_ws/src/venom_vnv
git submodule sync --recursive
make submodules-uav
```

`.gitmodules` 里的 URL 统一保留 HTTPS，保证任何机器都可以直接拉取。开发者本地如果需要推送，可以给主仓库或子模块配置 SSH `pushurl`。

### 如果你改的是主仓库内容

例如：

- `venom_bringup`
- `venom_robot_description`
- `docs/`
- 主仓库根目录脚本和配置

那么正常走主仓库的 fork / 分支 / PR 流程即可。

### 如果你改的是子模块内容

例如：

- `localization/lio/Point-LIO`
- `localization/lio/Fast-LIO`
- `driver/venom_serial_driver`
- `driver/scout_ros2`
- `driver/piper_ros`

那么正确流程是：

1. 先 fork 对应子模块仓库
2. 在子模块目录内把 `origin` 指到你自己的 fork
3. 提交子模块自己的 PR
4. 子模块改动确定后，再回到 `Venom_VNV` 主仓库更新子模块指针
5. 最后对主仓库再提一个 PR

### 不要把主仓库指向只存在于个人 fork 的子模块提交

主仓库里的子模块指针，原则上应该尽量指向：

- 已经进入组织仓库的提交
- 或者至少是团队内部明确约定会保留的提交

否则其他同学递归拉取时可能失败，CI 也可能找不到对应提交。

## Git 远端地址建议（主仓库 + 子模块）

如果你的机器还没配置 GitHub SSH 密钥，请先参考：

- [GitHub SSH 密钥配置完整教程（RSA 版本）](https://liyihan.xyz/archives/github-ssh-mi-yao-pei-zhi)

本项目推荐采用以下远端策略：

- `fetch/pull` 使用 HTTPS，便于任何机器直接拉取
- `push` 使用 SSH，便于开发机直接推送
- `.gitmodules` 中统一保留 HTTPS 地址，保证递归拉取时兼容性更好

当前新增子模块也遵守这条规则，例如 `perception/yolo_detector`、`simulation/venom_nav_simulation` 和 `planning/navigation/ego-planner-swarm` 都在 `.gitmodules` 中使用 HTTPS。

CI 和 Docker 构建脚本会临时写入 `COLCON_IGNORE` 来跳过硬件相关包或不适合当前平台的仿真包，`COLCON_IGNORE` 已被 `.gitignore` 忽略，不应提交进仓库。

## 一键统一主仓库与子模块远端

在仓库根目录执行以下命令，可同时修改主仓库和所有子模块的 `origin` / `pushurl`：

```bash
cd ~/venom_ws/src/venom_vnv

to_https() {
  echo "$1" | sed -E \
    's|^git@github.com:([^/]+/.+)\.git$|https://github.com/\1.git|; s|^git@github.com:([^/]+/.+)$|https://github.com/\1.git|'
}

to_ssh() {
  echo "$1" | sed -E \
    's|^https://github.com/([^/]+/.+)\.git$|git@github.com:\1.git|; s|^https://github.com/([^/]+/.+)$|git@github.com:\1.git|'
}

# 主仓库：pull/fetch 用 HTTPS，push 用 SSH
main_url="$(git remote get-url origin)"
main_https="$(to_https "$main_url")"
main_ssh="$(to_ssh "$main_https")"
git remote set-url origin "$main_https"
git remote set-url --push origin "$main_ssh"

# .gitmodules 中统一写 HTTPS，便于任何机器拉取
if [ -f .gitmodules ]; then
  while read -r key url; do
    git config -f .gitmodules "$key" "$(to_https "$url")"
  done < <(git config -f .gitmodules --get-regexp '^submodule\..*\.url$' || true)
  git submodule sync --recursive
fi

# 子模块工作树：origin 用 HTTPS，pushurl 用 SSH
git submodule foreach --recursive '
url="$(git config --get remote.origin.url 2>/dev/null || true)"
if [ -z "$url" ]; then
  url="$(git config -f "$toplevel/.gitmodules" --get "submodule.$name.url" 2>/dev/null || true)"
fi
if [ -n "$url" ]; then
  https="$(echo "$url" | sed -E "s|^git@github.com:([^/]+/.+)\\.git$|https://github.com/\\1.git|; s|^git@github.com:([^/]+/.+)$|https://github.com/\\1.git|")"
  ssh="$(echo "$https" | sed -E "s|^https://github.com/([^/]+/.+)\\.git$|git@github.com:\\1.git|; s|^https://github.com/([^/]+/.+)$|git@github.com:\\1.git|")"
  git remote set-url origin "$https"
  git remote set-url --push origin "$ssh"
fi
'
```

## 常用开发命令

### Docker 仿真与 CI 环境

当前仓库提供了基于 Docker 的 sim 环境，用于本地复现 CI 或做无头构建验证：

```bash
cd ~/venom_ws/src/venom_vnv
make build     # 构建 ghcr.io/venom-algorithm/venom_vnv/sim:latest
make up        # 启动 venom_sim 容器
make shell     # 进入容器
make rosdep    # 容器内安装 ROS 依赖
make colcon    # 容器内 colcon build
make ci-build  # 本地模拟 GitHub Actions 的无头构建
make clean     # 删除容器和 .ci_build
```

CI 构建会排除硬件驱动和 Gazebo Classic 相关包，重点验证主仓库中可在容器内稳定构建的部分。

### 首次编译

```bash
cp ~/venom_ws/src/venom_vnv/driver/livox_ros_driver2/package_ROS2.xml \
   ~/venom_ws/src/venom_vnv/driver/livox_ros_driver2/package.xml

cd ~/venom_ws
rosdep install -r --from-paths src --ignore-src --rosdistro $ROS_DISTRO -y
colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release -DROS_EDITION=ROS2 -DHUMBLE_ROS=humble
```

### 只编译自己改动的包

```bash
cd ~/venom_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install --packages-select <pkg_name>
```

### 删除构建产物后重编译

```bash
cd ~/venom_ws
rm -rf build install log
rosdep install -r --from-paths src --ignore-src --rosdistro $ROS_DISTRO -y
colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release -DROS_EDITION=ROS2 -DHUMBLE_ROS=humble
```

### 更新到主仓库与子模块最新版本

```bash
cd ~/venom_ws/src/venom_vnv
git pull
git submodule sync --recursive
git submodule update --init --recursive
```

## 常用调试工具

建议至少熟悉以下命令：

```bash
ros2 topic list
ros2 node list
ros2 topic echo /topic_name
ros2 interface show <msg_or_srv>
ros2 launch <pkg> <launch_file>
rviz2
rqt_graph
```

定位问题时，优先先看：

- 话题是否存在
- TF 是否连通
- frame_id 是否正确
- 参数文件是否加载成功
- 相关 launch 是否重复启动了同一个节点

## 文档开发与本地预览

如果你改的是 `docs/`，建议先本地预览再提交。

推荐使用 Docker 预览 GitHub Pages：

```bash
cd ~/venom_ws/src/venom_vnv
docker run --rm -it -p 4001:4000 -v "$PWD":/srv/jekyll jekyll/jekyll:pages sh -lc "apk add --no-cache ruby-webrick >/dev/null && jekyll serve --source docs --host 0.0.0.0"
```

然后在浏览器打开：

```text
http://localhost:4001/Venom_VNV/
```

## 提交前检查清单

提交前建议至少检查以下内容：

1. 改动是否只包含本次任务相关内容
2. 是否误改了不属于自己的子模块提交指针
3. 如果改了接口、话题、TF、参数，是否同步更新文档
4. 是否在自己的分支上，而不是 `master`
5. 是否写清楚了本次验证方式
6. 如果改的是文档，页面是否能本地正常打开

## 面向多人协作的附加建议

由于当前可能会有二十位左右同学并行开发，建议统一遵守：

- 一个任务对应一个分支
- 一个 PR 尽量只解决一个问题
- 接口改动必须提前沟通
- 子模块改动必须说明依赖的上游提交
- 不要直接把实验性代码堆进主分支
- 任何会影响其他同学联调的改动，都要写清楚迁移方法

## 相关文档

- [快速开始](../home/quick_start.md)
- [启动使用](../home/launch_usage.md)
- [贡献指南](contributing.md)
- [更新与迁移](migration_notes.md)
