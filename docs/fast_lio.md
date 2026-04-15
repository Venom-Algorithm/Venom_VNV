---
title: Fast-LIO
desc: Fast-LIO 接入说明与系统内接口约束。
breadcrumb: 模块与接口
layout: default
---

# Fast-LIO

当前仓库已经将 `Fast-LIO` 接入为 `lio/Fast-LIO` 子模块。

## 在系统中的定位

`Fast-LIO` 作为另一套 LIO 实现，后续接入时也应遵守统一的系统接口约束：

- 输出 `/odom`
- 发布 `odom -> base_link`
- 输出 `/cloud_registered`
- 配准点云 `frame_id` 统一为 `base_link`

## 相关文档

- [LIO 总览](lio_overview.md)
- [Point-LIO](point_lio.md)
