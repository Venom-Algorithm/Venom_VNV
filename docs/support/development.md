---
title: 开发说明
permalink: /development
desc: 面向开发机和协作者的 Git、远端地址与日常协作说明。
breadcrumb: 支持与社区
layout: default
---

## 适用场景

本页主要面向以下情况：

- 需要在开发机上长期维护本仓库
- 需要同时管理主仓库和多个子模块
- 需要统一 `pull/fetch` 与 `push` 的远端地址策略

如果你只是第一次部署使用本项目，优先查看 [快速开始]({{ '/quick_start' | relative_url }}).

## Git 远程地址建议（主仓库 + 子模块）

如果你的机器还没配置 GitHub SSH 密钥，请先参考：

- [GitHub SSH 密钥配置完整教程（RSA 版本）](https://liyihan.xyz/archives/github-ssh-mi-yao-pei-zhi)

本项目推荐采用以下远端策略：

- `fetch/pull` 使用 HTTPS，便于任何机器直接拉取
- `push` 使用 SSH，便于开发机直接推送
- `.gitmodules` 中统一保留 HTTPS 地址，保证递归拉取时兼容性更好

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

## 日常开发建议

- 部署机或演示机如果只需要拉代码，不强制配置 SSH
- 开发机如果需要频繁提交，建议尽早配好 SSH
- 子模块地址变更后，要同步检查 `.gitmodules`、本地工作树和文档说明
- 提交前建议先确认主仓库与子模块都位于预期分支和预期提交

## 相关文档

- [快速开始]({{ '/quick_start' | relative_url }})
- [更新与迁移]({{ '/migration_notes' | relative_url }})
- [贡献指南]({{ '/contributing' | relative_url }})
