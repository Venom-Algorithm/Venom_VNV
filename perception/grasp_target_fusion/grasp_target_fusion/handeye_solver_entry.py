import runpy
from pathlib import Path

from ament_index_python.packages import get_package_share_directory


def main() -> None:
    script_path = (
        Path(get_package_share_directory("grasp_target_fusion"))
        / "scripts"
        / "handeye_solver.py"
    )
    runpy.run_path(str(script_path), run_name="__main__")
