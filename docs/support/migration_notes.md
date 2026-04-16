---
title: 更新与迁移
permalink: /migration_notes
desc: 仓库地址迁移、submodule 策略与版本兼容说明。
breadcrumb: 支持与社区
layout: default
---

## 当前策略

- 主仓库与子模块维护在 organization 下
- `.gitmodules` 使用 HTTPS，方便非作者拉取
- 维护者本地 remote 可继续使用 SSH 进行推送

## 迁移时关注点

- 仓库地址切换后需要同步更新 `.gitmodules`
- 文档中的旧地址需要一起清理
- GitHub Pages 会递归拉取 submodule，因此 submodule 可访问性很重要
