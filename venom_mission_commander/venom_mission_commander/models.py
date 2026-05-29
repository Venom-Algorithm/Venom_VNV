from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class MissionState(str, Enum):
    IDLE = 'idle'
    RUNNING = 'running'
    NAVIGATING = 'navigating'
    EXECUTING_TASKS = 'executing_tasks'
    PAUSED = 'paused'
    EMERGENCY = 'emergency'
    COMPLETED = 'completed'
    COMPLETED_WITH_ERRORS = 'completed_with_errors'
    FAILED = 'failed'


class WaypointKind(str, Enum):
    PASS_THROUGH = 'pass_through'
    OPERATION_STOP = 'operation_stop'
    RETURN_PARK = 'return_park'


@dataclass
class TaskSpec:
    name: str
    task_type: str
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class WaypointSpec:
    name: str
    frame_id: str
    x: float
    y: float
    yaw: float
    kind: WaypointKind = WaypointKind.OPERATION_STOP
    tasks: list[TaskSpec] = field(default_factory=list)
    skip_navigation: bool = False
    description: str = ''
    nav_timeout_sec: float | None = None
    retry_count: int = 0


@dataclass
class MissionConfig:
    mission_id: str
    loop: bool
    stop_on_task_failure: bool
    waypoints: list[WaypointSpec]
    default_nav_timeout_sec: float | None = None
    default_retry_count: int = 0


@dataclass
class TaskExecutionResult:
    success: bool
    message: str = ''
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskContext:
    node: Any
    mission_id: str
    waypoint: WaypointSpec
    waypoint_index: int
    task_index: int
    mission_manager: Any
    blackboard: dict[str, Any]
