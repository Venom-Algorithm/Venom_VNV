---
title: 常见问题
permalink: /faq
desc: 初次部署与联调阶段最常见的问题汇总。
breadcrumb: 支持与社区
layout: default
---

## 仓库拉取失败怎么办

- 优先使用 HTTPS 地址拉取主仓库和 submodule
- 确认是否使用了 `--recurse-submodules`

## 编译失败怎么办

- 先执行 `rosdep install --from-paths . --ignore-src -r -y`
- 检查系统级 SDK 是否已经安装

## 设备连不上怎么办

- 雷达：先查 IP 与网卡
- 相机：先查 USB 枚举
- CAN：先查 `can0`
- 串口：先查设备名与权限

## 更多内容

- [故障排查]({{ '/troubleshooting' | relative_url }})
- [更新与迁移]({{ '/migration_notes' | relative_url }})
