"""Historical GICP relocalization bringup entry.

The small_gicp_relocalization stack is temporarily removed from the main
repository submodules because of known stability issues. Keep this launch file
as a stable entry name so future re-integration can happen without changing
upper-level scripts.
"""

_DISABLED_MESSAGE = (
    "GICP relocalization is temporarily disabled: "
    "small_gicp_relocalization is no longer a Venom_VNV submodule. "
    "Use Point-LIO odometry-only / async-map modes for current Mid360 tests, "
    "or re-enable the GICP stack after its stability issues are fixed."
)


def generate_launch_description():
    raise RuntimeError(_DISABLED_MESSAGE)
