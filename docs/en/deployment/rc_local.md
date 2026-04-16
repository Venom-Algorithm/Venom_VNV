---
title: rc.local
permalink: /en/rc_local
desc: Enable rc.local on Ubuntu 22.04 and use it for boot-time initialization such as network priority.
breadcrumb: Deployment & Usage
layout: default
---

## What `rc.local` Is Used For

`rc.local` is a traditional Linux startup script executed near the end of boot with root privileges. In this project, it is mainly useful for:

- Bringing up routes or CAN interfaces at boot
- Setting network priority
- Running repeatable initialization commands before user login

## Ubuntu 22.04 Notes

Ubuntu 22.04 does not enable `rc.local` by default. You need to create the file and enable the service manually.

## Create `/etc/rc.local`

```bash
sudo touch /etc/rc.local
sudo chmod 755 /etc/rc.local
echo '#!/bin/bash' | sudo tee /etc/rc.local
```

## Enable the `rc-local` Service

```bash
sudo cp /usr/lib/systemd/system/rc-local.service /etc/systemd/system/
```

Then edit:

```bash
sudoedit /etc/systemd/system/rc-local.service
```

Make sure the `[Install]` section contains:

```ini
[Install]
WantedBy=multi-user.target
```

## Start and Enable the Service

```bash
sudo systemctl start rc-local
sudo systemctl enable rc-local
sudo systemctl status rc-local
```

If the status shows `active (running)`, the service is available.

## Add Your Boot-Time Commands

Edit:

```bash
sudoedit /etc/rc.local
```

Example:

```bash
#!/bin/bash
echo "System booting..."
# add your initialization commands here
exit 0
```

Make sure `exit 0` is present at the end.

## Typical Use Cases in This Project

- Network priority adjustment for the MID360 NIC
- Static route restoration after reboot
- Chassis or arm CAN setup commands

## Related Pages

- [LiDAR Setup]({{ '/en/lidar_setup' | relative_url }})
- [Chassis CAN Setup]({{ '/en/chassis_can_setup' | relative_url }})
- [Arm CAN Setup]({{ '/en/piper_can_setup' | relative_url }})
