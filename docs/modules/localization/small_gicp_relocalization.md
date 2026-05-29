---
title: 重定位（暂停接入）
description: GICP 重定位模块当前因稳定性问题暂时从主仓库 submodule 中移除。
---

## 当前状态

`small_gicp_relocalization` 当前因稳定性问题暂时下线，不再作为 `Venom_VNV` 主仓库的 submodule 拉取。

这意味着：

- `.gitmodules` 中不再包含 `localization/relocalization/small_gicp_relocalization`
- `make submodules-ugv` 不再初始化该仓库
- 新工作区默认不会包含 `small_gicp_relocalization` 包
- 现有 `venom_bringup` 中的 relocalization launch 只作为历史入口保留，当前不推荐直接使用

## 后续恢复条件

重新接入前建议先解决以下问题：

1. 明确 `map -> odom` 发布策略，避免和 LIO / Nav2 的 TF 责任冲突
2. 补齐先验地图、输入点云、初值和 TF 缺失时的安全降级
3. 增加 bag 回放回归测试，覆盖低速、高速旋转和定位跳变场景
4. 确认节点在无 RViz、慢磁盘、空点云和 TF 超时时不会阻塞主链路

## 当前替代路径

如果只是验证 Mid360 + Point-LIO，请优先使用 LIO 模块本身输出 `odom -> base_link`，不要依赖 GICP 重定位修正。
