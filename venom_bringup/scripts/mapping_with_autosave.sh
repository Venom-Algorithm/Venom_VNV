#!/bin/bash

# 地图保存路径。可通过环境变量 MAP_PATH 覆盖。
MAP_PATH="${MAP_PATH:-$HOME/venom_ws/src/venom_vnv/localization/lio/Point-LIO/PCD/map_2d}"
SAVE_INTERVAL=5  # 每5秒保存一次
LAUNCH_FILE="${1:-scout_mini_mapping.launch.py}"

# 启动 mapping launch 文件
ros2 launch venom_bringup "$LAUNCH_FILE" &
LAUNCH_PID=$!

# 定期保存地图的后台任务
(
    # 等待节点启动
    sleep 10
    echo "开始定期保存地图（每${SAVE_INTERVAL}秒）..."

    while true; do
        echo "[$(date +%H:%M:%S)] 正在保存地图..."
        if ros2 service call /slam_toolbox/serialize_map slam_toolbox/srv/SerializePoseGraph "{filename: \"$MAP_PATH\"}" 2>&1 | grep -q "response"; then
            echo "[$(date +%H:%M:%S)] ✓ 地图保存成功"
        else
            echo "[$(date +%H:%M:%S)] ✗ 地图保存失败"
        fi
        sleep $SAVE_INTERVAL
    done
) &
SAVE_PID=$!

# 清理函数
cleanup() {
    echo "正在停止..."
    kill $SAVE_PID 2>/dev/null
    kill $LAUNCH_PID 2>/dev/null
    wait $LAUNCH_PID 2>/dev/null
    echo "已停止"
    exit 0
}

# 捕获 Ctrl+C
trap cleanup SIGINT SIGTERM

# 等待 launch 进程
wait $LAUNCH_PID
