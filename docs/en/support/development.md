---
title: Development Notes
description: Recommended environment baseline, common tools, Git workflow, submodule
  rules, and debugging notes for team development.
---

## Scope

This page is for:

- teams with many contributors working in parallel
- contributors maintaining the main repository, submodules, and docs
- long-lived Ubuntu + ROS 2 Humble development machines
- contributors using a fork-and-PR workflow

For first-time deployment, start with:

- [Quick Start](../home/quick_start.md)
- [Environment Setup](../deployment/environment.md)
- [LiDAR Setup](../deployment/lidar_setup.md)

## Recommended Baseline

| Item | Recommendation | Notes |
| --- | --- | --- |
| OS | Ubuntu 22.04 LTS | main project baseline |
| ROS | ROS 2 Humble | unified middleware baseline |
| Python | Python 3.10 | default on Ubuntu 22.04 |
| Build tools | `colcon`, `rosdep` | required for ROS 2 workspaces |
| Toolchain | GCC / G++ 11, CMake | system defaults are fine |
| Version control | Git + GitHub | fork, branch, PR, and submodule workflow |
| Editor | VS Code | recommended common editor |
| AI assistant | Codex | useful for reading, drafting, and small edits |
| Docs preview | Docker | recommended for local GitHub Pages preview |

## Module-Specific Dependencies

Not everyone needs every dependency. Install by task direction:

- Mid360 / Point-LIO / Fast-LIO:
  - `Livox-SDK2`
  - see [LiDAR Setup](../deployment/lidar_setup.md)
- RealSense D435i:
  - `librealsense2`
  - see [RealSense Setup](../deployment/realsense_setup.md)
- Chassis development:
  - `can-utils`
  - vendor SDK and driver dependencies
- Arm development:
  - Piper-related CAN environment
- PX4 / UAV work:
  - PX4, Micro XRCE-DDS Agent, and bridge-side dependencies
- Docs work:
  - Docker
  - Markdown editing environment
- Simulation work:
  - Gazebo and simulation workspace dependencies

## Recommended Workspace Layout

```text
~/venom_ws/
├── src/
│   └── venom_vnv/
└── build/ install/ log/
```

Recommended repository path:

```bash
~/venom_ws/src/venom_vnv
```

In each new terminal:

```bash
source /opt/ros/humble/setup.bash
source ~/venom_ws/install/setup.bash
```

If the workspace has not been built yet, the second line can be skipped temporarily.

## VS Code Notes

VS Code is recommended because it makes it easier to:

- search topics, TF names, and parameters across the whole repository
- work on Python, C++, YAML, and Markdown in one place
- review diffs and use an integrated terminal

Recommended extension categories:

- C / C++
- Python
- CMake
- YAML
- Markdown
- Git enhancement extensions
- ROS helper extensions

Daily usage recommendations:

- open the repository root as the workspace
- use global search before changing topics, TF names, or parameters
- inspect diffs before every commit
- do not edit generated files under `build/`, `install/`, or `log/`
- if you change launch files, yaml configs, or interfaces, check whether docs must be updated too

## Codex Usage Notes

If you use Codex in development:

- keep it inside your own fork and branch
- good use cases include:
  - documentation cleanup
  - parameter explanations
  - launch / yaml / markdown restructuring
  - large-scale renaming
  - reading one module and summarizing its interfaces
- do not let it commit or push blindly without your own review
- always review manually when the change involves:
  - remote URLs
  - submodule pointers
  - file deletion or broad refactors
  - topics, TF, frame IDs, or interface contracts
- after a Codex patch, still run:
  - `git diff`
  - targeted build or runtime checks
  - reproducibility checks for commands in docs

## GitHub Collaboration Model

Before direct write access is opened more broadly, contributors should follow:

```text
fork -> clone -> branch -> commit -> push -> Pull Request -> review -> merge
```

Each contributor should complete at least one full cycle first.

### 1. Fork the official repository

- official repository: `Venom-Algorithm/Venom_VNV`
- your fork: `<your-name>/Venom_VNV`

### 2. Clone your own fork

```bash
cd ~
mkdir -p ~/venom_ws/src
git clone --recurse-submodules https://github.com/<your-name>/Venom_VNV.git ~/venom_ws/src/venom_vnv
cd ~/venom_ws/src/venom_vnv
git remote add upstream https://github.com/Venom-Algorithm/Venom_VNV.git
git remote -v
```

Recommended convention:

- `origin` points to your fork
- `upstream` points to the organization repository

### 3. Sync upstream before new work

```bash
cd ~/venom_ws/src/venom_vnv
git fetch upstream
git checkout master
git merge --ff-only upstream/master
git push origin master
git submodule sync --recursive
git submodule update --init --recursive
```

### 4. Create a branch, do not work on `master`

```bash
cd ~/venom_ws/src/venom_vnv
git checkout -b feat/<short-topic>
```

Suggested branch names:

- `feat/<topic>`
- `fix/<topic>`
- `docs/<topic>`
- `refactor/<topic>`

## Task Management Recommendation

With many contributors in parallel, do not rely only on verbal coordination. Use GitHub Issues or GitHub Projects to track work.

Each task should ideally include:

| Field | Recommendation |
| --- | --- |
| Title | Write the module or concrete goal directly, for example `PX4 bridge integration` or `Ego-planner bring-in` |
| Owner | At least one primary owner |
| Layer | one of `driver`, `perception`, `localization`, `planning`, `system`, or `simulation` |
| Dependency | for example, “depends on Mid360 link validation first” |
| Code location | main repository or a specific submodule |
| Deliverable | code, docs, launch files, params, demo video, procurement list, and so on |
| Verification | at least one reproducible command or validation procedure |

Recommended project columns:

- `Todo`
- `In Progress`
- `Blocked`
- `Review`
- `Done`

These directions should usually be split into separate issues instead of one large task:

- mechanical frame and hardware integration
- planners such as Ego-planner, TEB, and MoveIt
- RTK, Mid360, Point-LIO, and Fast-LIO related localization work
- PX4 bridge, DDS Agent, and command-chain integration
- YOLO, QR code recognition, auto-aim, and payload perception tasks
- Gazebo, Isaac Sim, and `venom_nav_simulation` work

The point is practical: when many people edit the repository at the same time, ownership and status need to be visible.

## Submodule Rules

This repository includes many submodules, so the workflow matters.

### Profile-Based Submodule Checkout

If you only work on one area, you do not need to initialize every submodule. The root Makefile provides profile targets:

| Command | Use case |
| --- | --- |
| `make submodules-ugv` | real UGV: chassis, arm, LiDAR, camera, serial, localization, YOLO |
| `make submodules-sim` | pure simulation: `venom_nav_simulation` and `ego-planner-swarm` |
| `make submodules-ugv-sim` | UGV simulation: simulation, Point-LIO, Ego Planner, YOLO |
| `make submodules-auto-aim` | auto-aim development: `rm_auto_aim`, Hikrobot camera, serial |
| `make submodules-uav` | UAV development: PX4 bridge and Ego Planner |
| `make submodules-all` | initialize all submodules |

Example:

```bash
cd ~/venom_ws/src/venom_vnv
git submodule sync --recursive
make submodules-uav
```

URLs in `.gitmodules` stay HTTPS so any machine can clone the repository. Developers can configure SSH `pushurl` locally when they need push access.

### If you only change the main repository

Examples:

- `venom_bringup`
- `venom_robot_description`
- `docs/`
- root-level scripts and configs

Use the normal main-repo fork / branch / PR flow.

### If you change a submodule

Examples:

- `localization/lio/Point-LIO`
- `localization/lio/Fast-LIO`
- `driver/venom_serial_driver`
- `driver/scout_ros2`
- `driver/piper_ros`

Recommended workflow:

1. fork the submodule repository
2. point that submodule working tree to your fork
3. submit a PR for the submodule itself
4. once the submodule change is settled, update the submodule pointer in `Venom_VNV`
5. then open a PR for the main repository

### Do not point the main repository at a commit that exists only in your personal fork

The main repository should preferably reference submodule commits that already exist in the organization repository, or at least in a commit that the team has explicitly agreed to keep available.

## Remote URL Strategy

Current recommendation:

- HTTPS for `fetch` / `pull`
- SSH for `push`
- HTTPS URLs inside `.gitmodules`

New submodules follow the same rule, including `perception/yolo_detector`, `simulation/venom_nav_simulation`, and `planning/navigation/ego-planner-swarm`.

The CI and Docker build scripts may write `COLCON_IGNORE` files temporarily to skip hardware-only packages or platform-specific simulation packages. `COLCON_IGNORE` is ignored by `.gitignore` and should not be committed.

SSH key reference:

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

## Common Commands

### Docker Simulation and CI Environment

The root repository now includes a Docker-based sim environment for local CI reproduction and headless build checks:

```bash
cd ~/venom_ws/src/venom_vnv
make build     # build ghcr.io/venom-algorithm/venom_vnv/sim:latest
make up        # start the venom_sim container
make shell     # enter the container
make rosdep    # run rosdep inside the container
make colcon    # run colcon build inside the container
make ci-build  # run the same headless build flow used by GitHub Actions
make clean     # remove the container and .ci_build
```

The CI build skips hardware drivers and Gazebo Classic packages, and focuses on the parts that can be built reliably inside the container.

### First build

```bash
cp ~/venom_ws/src/venom_vnv/driver/livox_ros_driver2/package_ROS2.xml \
   ~/venom_ws/src/venom_vnv/driver/livox_ros_driver2/package.xml

cd ~/venom_ws
rosdep install -r --from-paths src --ignore-src --rosdistro $ROS_DISTRO -y
colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release -DROS_EDITION=ROS2 -DHUMBLE_ROS=humble
```

### Build only the packages you changed

```bash
cd ~/venom_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install --packages-select <pkg_name>
```

### Clean rebuild

```bash
cd ~/venom_ws
rm -rf build install log
rosdep install -r --from-paths src --ignore-src --rosdistro $ROS_DISTRO -y
colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release -DROS_EDITION=ROS2 -DHUMBLE_ROS=humble
```

### Update main repo and submodules

```bash
cd ~/venom_ws/src/venom_vnv
git pull
git submodule sync --recursive
git submodule update --init --recursive
```

## Common Debug Tools

Recommended basic commands:

```bash
ros2 topic list
ros2 node list
ros2 topic echo /topic_name
ros2 interface show <msg_or_srv>
ros2 launch <pkg> <launch_file>
rviz2
rqt_graph
```

When debugging, check these first:

- does the topic exist
- is the TF chain connected
- are frame IDs correct
- was the expected parameter file really loaded
- did the launch file start the same node twice

## Docs Preview

If you modify `docs/`, preview locally before opening a PR.

Recommended Docker command:

```bash
cd ~/venom_ws/src/venom_vnv
docker run --rm -it -p 4001:4000 -v "$PWD":/srv/jekyll jekyll/jekyll:pages sh -lc "apk add --no-cache ruby-webrick >/dev/null && jekyll serve --source docs --host 0.0.0.0"
```

Then open:

```text
http://localhost:4001/Venom_VNV/
```

## Pre-Submission Checklist

1. confirm the diff only contains task-related changes
2. confirm you did not accidentally move unrelated submodule pointers
3. if topics, TF, interfaces, or params changed, update docs too
4. confirm you are not working on `master`
5. describe how you verified the change
6. if you changed docs, preview the page locally

## Team-Scale Recommendations

With many contributors working in parallel:

- one task, one branch
- one PR should solve one clear problem
- interface changes should be discussed before merge
- submodule changes should mention the upstream commit dependency
- do not stack experimental changes directly into the main branch
- any change that affects other people's integration should include migration notes

## Related Pages

- [Quick Start](../home/quick_start.md)
- [Launch & Use](../home/launch_usage.md)
- [Contributing](contributing.md)
- [Updates & Migration](migration_notes.md)
