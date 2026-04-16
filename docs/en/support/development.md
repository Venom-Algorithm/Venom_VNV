---
title: Development Notes
permalink: /en/development
desc: Git remote strategy, submodule handling, and collaboration notes for development machines.
breadcrumb: Support & Community
layout: default
---

## Scope

This page is mainly for:

- long-lived development machines
- contributors working with the main repository plus submodules
- teams that want consistent fetch/pull/push remote conventions

For a pure deployment machine, [Quick Start]({{ '/en/quick_start' | relative_url }}) is usually enough.

## Recommended Remote Strategy

The project currently recommends:

- HTTPS for `fetch` / `pull`
- SSH for `push`
- HTTPS URLs inside `.gitmodules`

This keeps cloning simple for new machines while still making pushes convenient for developers.

## SSH Key Reference

- [GitHub SSH key setup guide](https://liyihan.xyz/archives/github-ssh-mi-yao-pei-zhi)

## One-Command Remote Rewrite

Run from the repository root:

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

main_url="$(git remote get-url origin)"
main_https="$(to_https "$main_url")"
main_ssh="$(to_ssh "$main_https")"
git remote set-url origin "$main_https"
git remote set-url --push origin "$main_ssh"

if [ -f .gitmodules ]; then
  while read -r key url; do
    git config -f .gitmodules "$key" "$(to_https "$url")"
  done < <(git config -f .gitmodules --get-regexp '^submodule\..*\.url$' || true)
  git submodule sync --recursive
fi

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
