from glob import glob
import os

from setuptools import find_packages, setup

package_name = "flame_arm_tracker"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
        (os.path.join("share", package_name, "config"), glob("config/*.yaml")),
        (os.path.join("share", package_name, "launch"), glob("launch/*.py")),
        (
            os.path.join("share", package_name, "models", "exp_256_openvino_model"),
            glob("models/exp_256_openvino_model/*"),
        ),
    ],
    install_requires=["setuptools", "ament_index_python"],
    zip_safe=True,
    maintainer="lzx2530",
    maintainer_email="2893478728@qq.com",
    description="Color flame-picture detection and Piper arm visual tracking.",
    license="MIT",
    entry_points={
        "console_scripts": [
            "flame_color_detector = flame_arm_tracker.flame_color_detector:main",
            "flame_yolo_detector = flame_arm_tracker.flame_yolo_detector:main",
            "flame_arm_tracker = flame_arm_tracker.flame_arm_tracker_node:main",
            "color_box_detector = flame_arm_tracker.color_box_detector:main",
        ],
    },
)
