#!/bin/bash

PCD_DIR="${PCD_DIR:-$HOME/venom_ws/src/venom_vnv/localization/lio/Point-LIO/PCD}"
TIMESTAMP=$(date +"%Y%m%d_%H%M")

# 备份3D点云
SOURCE_PCD="$PCD_DIR/scans.pcd"
BACKUP_PCD="$PCD_DIR/scans_${TIMESTAMP}.pcd"

if [ -f "$SOURCE_PCD" ]; then
    cp "$SOURCE_PCD" "$BACKUP_PCD"
    echo "备份完成: $BACKUP_PCD"
else
    echo "警告: 3D点云文件不存在 $SOURCE_PCD"
fi

# 备份2D地图
MAP_2D_POSEGRAPH="$PCD_DIR/map_2d.posegraph"
MAP_2D_DATA="$PCD_DIR/map_2d.data"

if [ -f "$MAP_2D_POSEGRAPH" ] && [ -f "$MAP_2D_DATA" ]; then
    cp "$MAP_2D_POSEGRAPH" "$PCD_DIR/map_2d_${TIMESTAMP}.posegraph"
    cp "$MAP_2D_DATA" "$PCD_DIR/map_2d_${TIMESTAMP}.data"
    echo "备份完成: map_2d_${TIMESTAMP}.posegraph 和 map_2d_${TIMESTAMP}.data"
else
    echo "警告: 2D地图文件不存在"
fi
