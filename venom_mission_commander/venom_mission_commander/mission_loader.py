import math
from pathlib import Path
from typing import Any

import yaml

from venom_mission_commander.models import MissionConfig, TaskSpec, WaypointKind, WaypointSpec


class MissionLoader:
    def load(self, config_path: str) -> MissionConfig:
        raw = self._read_yaml(config_path)
        mission_raw = raw.get('mission', {})
        waypoint_raw_list = raw.get('waypoints', [])
        default_nav_timeout_sec = self._parse_optional_positive_float(
            mission_raw.get('nav_timeout_sec'),
            'mission.nav_timeout_sec',
        )
        default_retry_count = self._parse_non_negative_int(
            mission_raw.get('retry_count', 0),
            'mission.retry_count',
        )

        if not waypoint_raw_list:
            raise ValueError(f'No waypoints found in mission config: {config_path}')

        return MissionConfig(
            mission_id=str(mission_raw.get('id', 'venom_mission_commander')),
            loop=bool(mission_raw.get('loop', False)),
            stop_on_task_failure=bool(mission_raw.get('stop_on_task_failure', True)),
            waypoints=[
                self._parse_waypoint(item, default_nav_timeout_sec, default_retry_count)
                for item in waypoint_raw_list
            ],
            default_nav_timeout_sec=default_nav_timeout_sec,
            default_retry_count=default_retry_count,
        )

    def _parse_waypoint(
        self,
        raw: dict[str, Any],
        default_nav_timeout_sec: float | None,
        default_retry_count: int,
    ) -> WaypointSpec:
        required_keys = ['name', 'x', 'y']
        missing_keys = [key for key in required_keys if key not in raw]
        if missing_keys:
            raise ValueError(f'Waypoint is missing required keys: {missing_keys}')

        waypoint_name = str(raw['name'])
        return WaypointSpec(
            name=waypoint_name,
            frame_id=str(raw.get('frame_id', 'map')),
            x=float(raw['x']),
            y=float(raw['y']),
            yaw=float(raw.get('yaw', 0.0)),
            kind=self._parse_waypoint_kind(raw.get('kind', WaypointKind.OPERATION_STOP.value)),
            tasks=[self._parse_task(item) for item in raw.get('tasks', [])],
            skip_navigation=bool(raw.get('skip_navigation', False)),
            description=str(raw.get('description', '')),
            nav_timeout_sec=self._parse_optional_positive_float(
                raw.get('nav_timeout_sec', default_nav_timeout_sec),
                f'waypoint.{waypoint_name}.nav_timeout_sec',
            ),
            retry_count=self._parse_non_negative_int(
                raw.get('retry_count', default_retry_count),
                f'waypoint.{waypoint_name}.retry_count',
            ),
        )

    def _parse_waypoint_kind(self, raw_kind: Any) -> WaypointKind:
        try:
            return WaypointKind(str(raw_kind))
        except ValueError as exc:
            allowed = ', '.join(kind.value for kind in WaypointKind)
            raise ValueError(f'Unknown waypoint kind: {raw_kind}; allowed: {allowed}') from exc

    def _parse_optional_positive_float(self, raw_value: Any, field_name: str) -> float | None:
        if raw_value is None:
            return None

        value = float(raw_value)
        if not math.isfinite(value) or value <= 0.0:
            raise ValueError(f'{field_name} must be finite and positive when set; got {raw_value}')
        return value

    def _parse_non_negative_int(self, raw_value: Any, field_name: str) -> int:
        if isinstance(raw_value, bool):
            raise ValueError(f'{field_name} must be a non-negative integer; got {raw_value}')
        if isinstance(raw_value, int):
            value = raw_value
        elif isinstance(raw_value, str) and raw_value.isdecimal():
            value = int(raw_value)
        else:
            raise ValueError(f'{field_name} must be a non-negative integer; got {raw_value}')

        if value < 0:
            raise ValueError(f'{field_name} must be non-negative; got {raw_value}')
        return value

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
