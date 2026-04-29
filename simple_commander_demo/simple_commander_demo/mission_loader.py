from pathlib import Path
from typing import Any

import yaml

from simple_commander_demo.models import MissionConfig, TaskSpec, WaypointSpec


class MissionLoader:
    def load(self, config_path: str) -> MissionConfig:
        raw = self._read_yaml(config_path)
        mission_raw = raw.get('mission', {})
        waypoint_raw_list = raw.get('waypoints', [])

        if not waypoint_raw_list:
            raise ValueError(f'No waypoints found in mission config: {config_path}')

        return MissionConfig(
            mission_id=str(mission_raw.get('id', 'simple_commander_demo')),
            loop=bool(mission_raw.get('loop', False)),
            stop_on_task_failure=bool(mission_raw.get('stop_on_task_failure', True)),
            waypoints=[self._parse_waypoint(item) for item in waypoint_raw_list],
        )

    def _parse_waypoint(self, raw: dict[str, Any]) -> WaypointSpec:
        required_keys = ['name', 'x', 'y']
        missing_keys = [key for key in required_keys if key not in raw]
        if missing_keys:
            raise ValueError(f'Waypoint is missing required keys: {missing_keys}')

        return WaypointSpec(
            name=str(raw['name']),
            frame_id=str(raw.get('frame_id', 'map')),
            x=float(raw['x']),
            y=float(raw['y']),
            yaw=float(raw.get('yaw', 0.0)),
            tasks=[self._parse_task(item) for item in raw.get('tasks', [])],
            skip_navigation=bool(raw.get('skip_navigation', False)),
            description=str(raw.get('description', '')),
        )

    def _parse_task(self, raw: dict[str, Any]) -> TaskSpec:
        if 'type' not in raw:
            raise ValueError(f'Task is missing required key: type; raw={raw}')

        reserved_keys = {'name', 'type'}
        params = {
            key: value
            for key, value in raw.items()
            if key not in reserved_keys
        }

        return TaskSpec(
            name=str(raw.get('name', raw['type'])),
            task_type=str(raw['type']),
            params=params,
        )

    def _read_yaml(self, config_path: str) -> dict[str, Any]:
        path = Path(config_path).expanduser()
        if not path.is_file():
            raise FileNotFoundError(f'Mission config not found: {path}')

        with path.open('r', encoding='utf-8') as file_obj:
            data = yaml.safe_load(file_obj) or {}

        if not isinstance(data, dict):
            raise ValueError(f'Mission config must be a YAML dictionary: {path}')

        return data
