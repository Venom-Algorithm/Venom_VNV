from time import time
from typing import Any

from simple_commander_demo.models import MissionConfig, MissionState


class MissionManager:
    def __init__(self, logger: Any | None = None):
        self.logger = logger
        self.mission_id: str | None = None
        self.state = MissionState.IDLE
        self.state_data: dict[str, Any] = {}
        self.history: list[dict[str, Any]] = []

    def create_mission(self, mission_config: MissionConfig) -> None:
        self.mission_id = mission_config.mission_id
        self.state = MissionState.IDLE
        self.state_data = {
            'mission_id': mission_config.mission_id,
            'current_waypoint_index': None,
            'current_waypoint_name': None,
            'current_task_index': None,
            'current_task_name': None,
            'phase': 'created',
            'loop': mission_config.loop,
        }
        self.history = []

    def transition_to(self, new_state: MissionState, reason: str = '') -> None:
        old_state = self.state
        self.state = new_state
        event = {
            'time': time(),
            'from': old_state.value,
            'to': new_state.value,
            'reason': reason,
        }
        self.history.append(event)
        if self.logger is not None:
            self.logger.info(
                f'Mission state: {old_state.value} -> {new_state.value}'
                + (f' ({reason})' if reason else '')
            )

    def save_state(self, **kwargs: Any) -> None:
        self.state_data.update(kwargs)
        self.state_data['updated_at'] = time()

    def restore_state(self) -> dict[str, Any]:
        return dict(self.state_data)

    def mark_waypoint_started(self, waypoint_index: int, waypoint_name: str) -> None:
        self.save_state(
            current_waypoint_index=waypoint_index,
            current_waypoint_name=waypoint_name,
            current_task_index=None,
            current_task_name=None,
            phase='navigating',
        )
        self.transition_to(MissionState.NAVIGATING, f'waypoint={waypoint_name}')

    def mark_task_started(self, task_index: int, task_name: str) -> None:
        self.save_state(
            current_task_index=task_index,
            current_task_name=task_name,
            phase='executing_task',
        )
        self.transition_to(MissionState.EXECUTING_TASKS, f'task={task_name}')

    def mark_waypoint_done(self, waypoint_index: int, waypoint_name: str) -> None:
        self.save_state(
            current_waypoint_index=waypoint_index,
            current_waypoint_name=waypoint_name,
            current_task_index=None,
            current_task_name=None,
            phase='waypoint_done',
            last_completed_waypoint=waypoint_name,
        )

    def mark_mission_completed(self) -> None:
        self.save_state(phase='completed')
        if self.state_data.get('had_task_failure', False):
            self.transition_to(
                MissionState.COMPLETED_WITH_ERRORS,
                'all waypoints completed with task failures',
            )
            return

        self.transition_to(MissionState.COMPLETED, 'all waypoints completed')

    def mark_task_failed(self, task_name: str, task_type: str, message: str) -> None:
        failed_tasks = list(self.state_data.get('failed_tasks', []))
        failed_tasks.append({
            'task_name': task_name,
            'task_type': task_type,
            'message': message,
            'time': time(),
        })
        self.save_state(
            had_task_failure=True,
            failed_tasks=failed_tasks,
            last_task_success=False,
            last_task_message=message,
        )

    def fail(self, reason: str) -> None:
        self.save_state(phase='failed', failure_reason=reason)
        self.transition_to(MissionState.FAILED, reason)

    def summarize(self) -> dict[str, Any]:
        return {
            'mission_id': self.mission_id,
            'state': self.state.value,
            'state_data': self.restore_state(),
            'history': list(self.history),
        }
