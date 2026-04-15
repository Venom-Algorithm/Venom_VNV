---
title: 快速开始
desc: 面向第一次使用者的最短上手路径。
breadcrumb: 部署与使用
layout: default
---

## 开始之前

请先确认以下工具已经可用：

- ROS 2 Humble
- `rosdep`
- `colcon`
- Livox-SDK2

可以先用下面的方式确认 Livox-SDK2 已安装：

```bash
ldconfig -p | grep LivoxSdkCore
```

如果还没有安装，请先参考 [装配配置](setup.md) 完成 Livox-SDK2 安装。

如果 `rosdep install` 过程中报错，建议先尝试：

```bash
sudo rosdep init
rosdep update
```

## 推荐安装方式

如果你之前有旧工作区，建议先清理后重新拉取：

注意：如果你当前终端正好停留在 `~/venom_ws` 或它的子目录里，删除前请先切回家目录，否则删完后当前 shell 会处在一个失效路径中，后续 `git` 可能报 `Unable to read current working directory`。

```bash
cd ~
rm -rf ~/venom_ws
mkdir -p ~/venom_ws/src
git clone --recurse-submodules https://github.com/Venom-Algorithm/Venom_VNV ~/venom_ws/src/venom_vnv
cp ~/venom_ws/src/venom_vnv/driver/livox_ros_driver2/package_ROS2.xml \
   ~/venom_ws/src/venom_vnv/driver/livox_ros_driver2/package.xml

cd ~/venom_ws
rosdep install -r --from-paths src --ignore-src --rosdistro $ROS_DISTRO -y
colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release -DROS_EDITION=ROS2 -DHUMBLE_ROS=humble
```

编译完成后：

```bash
source ~/venom_ws/install/setup.bash
```

## Git 远程地址建议（主仓库 + 子模块）

如果你的机器还没配置 GitHub SSH 密钥，请先参考：

- [GitHub SSH 密钥配置完整教程（RSA 版本）](https://liyihan.xyz/archives/github-ssh-mi-yao-pei-zhi)

配置好 SSH 后，建议将本项目统一设置为：

- `fetch/pull` 走 HTTPS（未配置 SSH 的机器也能拉取）
- `push` 走 SSH（开发机推送更方便）

在仓库根目录执行以下一键命令，可同时修改主仓库和所有子模块的 `origin`：

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

# .gitmodules 里的 URL 统一改为 HTTPS，便于任何机器拉取
if [ -f .gitmodules ]; then
  while read -r key url; do
    git config -f .gitmodules "$key" "$(to_https "$url")"
  done < <(git config -f .gitmodules --get-regexp '^submodule\..*\.url$' || true)
  git submodule sync --recursive
fi

# 子模块工作树：同样设置 origin 为 HTTPS + pushurl 为 SSH
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

## 推荐阅读顺序

1. [环境准备]({{ '/environment' | relative_url }})
2. [硬件部署]({{ '/hardware_setup' | relative_url }})
3. [软件部署]({{ '/software_setup' | relative_url }})
4. [启动使用]({{ '/launch_usage' | relative_url }})

## 首次验证

- 雷达链路：参考 [Livox 雷达驱动](livox_ros_driver2.md)
- 相机链路：参考 [海康相机驱动](ros2_hik_camera.md)
- 串口链路：参考 [串口通信驱动](venom_serial_driver.md)
- 系统级数据流：参考 [话题与 TF 总览]({{ '/system_overview' | relative_url }})
