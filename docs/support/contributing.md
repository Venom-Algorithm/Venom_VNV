---
title: 贡献指南
description: 面向协作者的 fork、分支、Pull Request、文档同步与子模块提交流程约定。
---

## 基本原则

- 默认先 fork，再在自己的仓库里开发
- 默认通过 Pull Request 合并，不直接改组织仓库
- 一个分支只做一件事
- 一个 PR 尽量只解决一个明确问题

## 首次协作流程

建议每位新成员至少完整经历一次：

```text
fork -> clone -> branch -> commit -> push -> Pull Request -> review -> merge
```

在这条流程完整跑通之前，默认不开主仓库直接写权限。

## 分支建议

推荐命名：

- `feat/<topic>`
- `fix/<topic>`
- `docs/<topic>`
- `refactor/<topic>`

不要直接在 `master` 上开发。

## 提交信息建议

推荐使用清晰的前缀：

- `feat:`
- `fix:`
- `docs:`
- `refactor:`
- `chore:`

例如：

```text
docs: update developer onboarding guide
fix: unify point lio published frame ids
```

## Pull Request 建议

PR 描述里最好说明：

1. 改了什么
2. 为什么要改
3. 怎么验证
4. 是否影响话题、TF、参数、launch 或文档

## 文档同步要求

以下情况通常要同步更新文档：

- 新增或删除模块
- 修改启动命令
- 修改参数文件位置
- 修改话题名、TF、frame_id
- 修改子模块地址或组织方式

## 子模块提交流程

如果你改的是子模块：

1. 先 fork 对应子模块仓库
2. 在子模块仓库完成修改并提 PR
3. 子模块提交稳定后，再回主仓库更新子模块指针
4. 最后为主仓库再提一个 PR

不要让主仓库引用只存在于个人 fork 的子模块提交，除非已经明确协调。

## 合并前自查

- 是否只提交了和本任务相关的文件
- 是否误带了 `build/`、`install/`、`log/` 生成文件
- 是否误改了无关子模块指针
- 是否在自己的分支上
- 是否补充了必要文档

## 相关文档

- [开发说明](development.md)
- [快速开始](../home/quick_start.md)
- [更新与迁移](migration_notes.md)
