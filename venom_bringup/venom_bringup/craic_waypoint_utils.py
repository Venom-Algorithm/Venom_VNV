"""Utilities for loading CRAIC waypoint tasks."""

from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
from typing import List, Sequence


EARTH_RADIUS_METERS = 6378137.0

ACTION_LABELS = {
    0: 'unknown',
    1: 'straight',
    2: 'turn_right',
    3: 'turn_left',
    4: 'lane_change_left',
    5: 'lane_change_right',
    6: 'overtake',
    7: 'u_turn',
    8: 'park',
}


@dataclass(frozen=True)
class CraicWaypoint:
    """One parsed CRAIC waypoint."""

    index: int
    x: float
    y: float
    yaw: float
    action: int
    source_a: float
    source_b: float
    action_label: str


def _normalize_angle(angle: float) -> float:
    return math.atan2(math.sin(angle), math.cos(angle))


def infer_coordinate_mode(value_a: float, value_b: float) -> str:
    """Infer whether a row looks like lon/lat or planar coordinates."""
    if -180.0 <= value_a <= 180.0 and -90.0 <= value_b <= 90.0:
        if abs(value_a) > 20.0 or abs(value_b) > 20.0:
            return 'geodetic'
    return 'cartesian_m'


def geodetic_to_local_xy(
    longitude_deg: float,
    latitude_deg: float,
    origin_longitude_deg: float,
    origin_latitude_deg: float,
    map_origin_yaw_rad: float,
    map_origin_x_m: float,
    map_origin_y_m: float,
) -> tuple[float, float]:
    """Project lon/lat into a local ENU-style planar map frame."""
    lon = math.radians(longitude_deg)
    lat = math.radians(latitude_deg)
    lon0 = math.radians(origin_longitude_deg)
    lat0 = math.radians(origin_latitude_deg)

    east = (lon - lon0) * math.cos((lat + lat0) * 0.5) * EARTH_RADIUS_METERS
    north = (lat - lat0) * EARTH_RADIUS_METERS

    cos_yaw = math.cos(map_origin_yaw_rad)
    sin_yaw = math.sin(map_origin_yaw_rad)

    map_x = map_origin_x_m + cos_yaw * east + sin_yaw * north
    map_y = map_origin_y_m - sin_yaw * east + cos_yaw * north
    return map_x, map_y


def _compute_yaws(points_xy: Sequence[tuple[float, float]]) -> List[float]:
    if not points_xy:
        return []
    if len(points_xy) == 1:
        return [0.0]

    yaws: List[float] = []
    for idx, (x_value, y_value) in enumerate(points_xy):
        if idx < len(points_xy) - 1:
            next_x, next_y = points_xy[idx + 1]
            yaw = math.atan2(next_y - y_value, next_x - x_value)
        else:
            prev_x, prev_y = points_xy[idx - 1]
            yaw = math.atan2(y_value - prev_y, x_value - prev_x)
        yaws.append(_normalize_angle(yaw))
    return yaws


def load_craic_waypoints(
    file_path: str,
    coordinate_mode: str = 'geodetic',
    origin_longitude_deg: float = 0.0,
    origin_latitude_deg: float = 0.0,
    map_origin_yaw_rad: float = 0.0,
    map_origin_x_m: float = 0.0,
    map_origin_y_m: float = 0.0,
    use_first_waypoint_as_origin: bool = True,
) -> List[CraicWaypoint]:
    """Load the competition waypoint.txt file."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f'Waypoint file not found: {file_path}')

    parsed_rows = []
    for line_no, raw_line in enumerate(path.read_text(encoding='utf-8').splitlines(), start=1):
        stripped = raw_line.strip()
        if not stripped or stripped.startswith('#'):
            continue

        fields = stripped.replace(',', ' ').split()
        if len(fields) < 4:
            raise ValueError(
                f'Invalid waypoint row at line {line_no}: expected at least 4 fields, got {len(fields)}'
            )

        try:
            seq = int(fields[0])
            value_a = float(fields[1])
            value_b = float(fields[2])
            action = int(fields[3])
        except ValueError as exc:
            raise ValueError(f'Failed to parse waypoint row at line {line_no}: {stripped}') from exc

        parsed_rows.append((seq, value_a, value_b, action))

    if not parsed_rows:
        raise ValueError(f'Waypoint file is empty: {file_path}')

    resolved_mode = coordinate_mode
    if coordinate_mode == 'auto':
        resolved_mode = infer_coordinate_mode(parsed_rows[0][1], parsed_rows[0][2])

    if resolved_mode not in {'geodetic', 'cartesian_m', 'cartesian_cm'}:
        raise ValueError(
            f'Unsupported coordinate_mode "{coordinate_mode}". '
            'Use geodetic, cartesian_m, cartesian_cm, or auto.'
        )

    if resolved_mode == 'geodetic' and use_first_waypoint_as_origin:
        if math.isclose(origin_longitude_deg, 0.0) and math.isclose(origin_latitude_deg, 0.0):
            origin_longitude_deg = parsed_rows[0][1]
            origin_latitude_deg = parsed_rows[0][2]

    points_xy = []
    for _, value_a, value_b, _ in parsed_rows:
        if resolved_mode == 'geodetic':
            x_value, y_value = geodetic_to_local_xy(
                longitude_deg=value_a,
                latitude_deg=value_b,
                origin_longitude_deg=origin_longitude_deg,
                origin_latitude_deg=origin_latitude_deg,
                map_origin_yaw_rad=map_origin_yaw_rad,
                map_origin_x_m=map_origin_x_m,
                map_origin_y_m=map_origin_y_m,
            )
        elif resolved_mode == 'cartesian_cm':
            x_value = value_a * 0.01
            y_value = value_b * 0.01
        else:
            x_value = value_a
            y_value = value_b
        points_xy.append((x_value, y_value))

    yaws = _compute_yaws(points_xy)
    result = []
    for idx, (seq, value_a, value_b, action) in enumerate(parsed_rows):
        result.append(
            CraicWaypoint(
                index=seq,
                x=points_xy[idx][0],
                y=points_xy[idx][1],
                yaw=yaws[idx],
                action=action,
                source_a=value_a,
                source_b=value_b,
                action_label=ACTION_LABELS.get(action, f'action_{action}'),
            )
        )
    return result
