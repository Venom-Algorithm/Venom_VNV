"""Historical Scout Mini GICP relocalization bringup entry.

The small_gicp_relocalization stack is temporarily removed from the main
repository submodules because of known stability issues. Keep this launch file
as a stable entry name so future Scout Mini relocalization integration can be
restored without changing upper-level scripts.
"""

_DISABLED_MESSAGE = (
    "Scout Mini GICP relocalization is temporarily disabled: "
    "small_gicp_relocalization is no longer a Venom_VNV submodule. "
    "Use the mapping / odometry launch files for current tests, "
    "or re-enable the GICP stack after its stability issues are fixed."
)


def generate_launch_description():
    raise RuntimeError(_DISABLED_MESSAGE)
