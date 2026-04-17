# Compatibility

This file pins the supported PX4/ROS 2 compatibility line for the VNV PX4 project.

## Pinned Baseline

| Item | Value |
|------|-------|
| Ubuntu | `22.04` |
| ROS 2 | `Humble` |
| PX4 firmware line | `v1.16.x` |
| `px4_msgs` upstream branch | `release/1.16` |
| `px4_msgs` upstream base commit | `392e831c1f659429ca83902e66820d7094591410` |
| XRCE-DDS agent | `Micro XRCE-DDS Agent v2.4.3` |

## Compatibility Rule

The `px4_msgs` package in this project must stay aligned with the PX4 firmware message line.

For this project version:

- use PX4 `v1.16.x`
- use `px4_msgs` generated from `release/1.16`

If firmware and message definitions diverge, PX4 official ROS 2 docs describe using a translation-node path for message-version compatibility.

This project deliberately avoids that extra layer in v1 and instead pins one clean compatibility line.

## Internal Package Contract

- `px4_msgs/` should remain a vendored upstream package with minimal local edits
- `venom_px4_bridge/` is where VNV-specific logic belongs
- upper-level VNV code should not depend directly on vendored file paths

## Upgrade Policy

When upgrading to a new PX4 line:

1. choose the target PX4 firmware release line
2. update vendored `px4_msgs` from the matching upstream branch
3. update this file with the new upstream base commit
4. rebuild `px4_msgs` and `venom_px4_bridge`
5. verify `/fmu/out/*` visibility and bridge outputs in SITL before hardware testing
