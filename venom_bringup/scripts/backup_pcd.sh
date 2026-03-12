#!/bin/bash

SOURCE_FILE="lio/Point-LIO/PCD/scans.pcd"
TIMESTAMP=$(date +"%Y%m%d_%H%M")
BACKUP_FILE="lio/Point-LIO/PCD/scans_${TIMESTAMP}.pcd"

if [ -f "$SOURCE_FILE" ]; then
    cp "$SOURCE_FILE" "$BACKUP_FILE"
    echo "备份完成: $BACKUP_FILE"
else
    echo "错误: 源文件不存在 $SOURCE_FILE"
    exit 1
fi
