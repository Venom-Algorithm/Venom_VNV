---
title: 仿真层
description: 与真实部署链路解耦的仿真工作区与仿真基线总览。
---

## 层级职责

仿真层负责：

- 在不接真实硬件的情况下验证定位、导航和系统流程
- 承载仿真世界、地图、模型和仿真专用 launch
- 作为算法回归和参数联调的独立环境

## 当前子项目

- [导航仿真工作区](venom_nav_simulation.md)

## 为什么单独成层

仿真工作区和真实部署工作区的依赖、资源文件和运行方式差异很大。

把仿真层单独拿出来，主要是为了：

1. 避免仿真资源污染主部署工作区
2. 保持导航/LIO 回归环境稳定
3. 让 Sim2Real 的边界更清楚

## 当前目录映射

- `simulation/venom_nav_simulation`
- `docker/Dockerfile.sim`
- `docker-compose.yml`
- `scripts/ci-colcon-build.sh`

## Docker 仿真环境

主仓库新增了 Docker sim 环境，用于统一仿真依赖和本地复现 CI 构建：

```bash
cd ~/venom_ws/src/venom_vnv
make build
make up
make shell
make rosdep
make colcon
```

需要模拟 GitHub Actions 的无头构建时：

```bash
cd ~/venom_ws/src/venom_vnv
make ci-build
```

清理容器和构建缓存：

```bash
cd ~/venom_ws/src/venom_vnv
make clean
```

当前 CI 会临时给硬件驱动、LIO 子模块和 Gazebo Classic 相关包写入 `COLCON_IGNORE`，只验证容器中可稳定构建的部分。

## 推荐使用方式

如果要验证：

- `MID360 + Gazebo + LIO + Nav2`
- 地图回归
- 参数联调
- Docker / CI 构建复现

优先从仿真层进入，而不是把这些流程塞进 `venom_bringup` 主工作区。

## 相关页面

- [总体架构](../architecture.md)
- [定位层](../localization/index.md)
- [规划层](../planning/index.md)
