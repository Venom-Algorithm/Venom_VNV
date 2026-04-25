---
title: 更新与迁移
description: 仓库地址迁移、submodule 策略与版本兼容说明。
---

## 当前策略

- 主仓库与子模块维护在 organization 下
- `.gitmodules` 使用 HTTPS，方便非作者拉取
- 维护者本地 remote 可继续使用 SSH 进行推送
- 按需拉取子模块时优先使用 Makefile profile，例如 `make submodules-uav`
- CI / Docker 构建会临时写入 `COLCON_IGNORE` 跳过硬件或平台相关包，该文件不应提交

## 近期结构变化

| 变化 | 说明 |
| --- | --- |
| `planning/navigation/ego-planner-swarm` | 新增 Ego Planner Swarm ROS 2 子模块，跟踪 `ros2_version` 分支 |
| `venom_bringup/launch/examples/px4_vps_bridge.launch.py` | 新增 PX4 外部位姿桥接入口 |
| `docker/Dockerfile.sim`、`docker-compose.yml` | 新增 Docker sim 环境 |
| `Makefile` profile | 新增 `submodules-ugv`、`submodules-sim`、`submodules-uav` 等按需拉取命令 |

## 迁移时关注点

- 仓库地址切换后需要同步更新 `.gitmodules`
- 文档中的旧地址需要一起清理
- GitHub Pages 会递归拉取 submodule，因此 submodule 可访问性很重要
- 如果只初始化了部分子模块，切换任务方向后需要重新执行对应 `make submodules-*`
