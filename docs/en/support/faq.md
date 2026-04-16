---
title: FAQ
permalink: /en/faq
desc: The most common issues during initial deployment and integration.
breadcrumb: Support & Community
layout: default
---

## Repository clone fails

- Prefer HTTPS URLs for the main repository and submodules
- Confirm whether `--recurse-submodules` was used when required

## Build fails

- Run `rosdep install --from-paths . --ignore-src -r -y`
- Check whether system-level SDKs have already been installed

## A device does not come online

- LiDAR: check IP and NIC settings first
- Camera: check USB enumeration first
- CAN: check `can0` or the renamed interface first
- Serial: check the device path and permissions first

## More

- [Troubleshooting]({{ '/en/troubleshooting' | relative_url }})
- [Updates & Migration]({{ '/en/migration_notes' | relative_url }})
