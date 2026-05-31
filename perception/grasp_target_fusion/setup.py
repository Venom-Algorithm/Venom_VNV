from glob import glob
import os

from setuptools import find_packages, setup

package_name = "grasp_target_fusion"


setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
        (f"share/{package_name}", ["README.md"]),
        (os.path.join("share", package_name, "launch"), glob("launch/*.py")),
        (os.path.join("share", package_name, "config"), glob("config/*.yaml")),
        (os.path.join("share", package_name, "handeye"), glob("handeye/*.yaml")),
        (os.path.join("share", package_name, "scripts"), glob("scripts/*.py")),
    ],
    install_requires=["setuptools", "ament_index_python"],
    zip_safe=True,
    maintainer="lzx2530",
    maintainer_email="2893478728@qq.com",
    description="Bridge 2D detections and D435i depth into grasp targets.",
    license="MIT",
    entry_points={
        "console_scripts": [
            "grasp_target_fusion = grasp_target_fusion.grasp_target_fusion_node:main",
            "fake_detection_publisher = grasp_target_fusion.fake_detection_publisher:main",
            "fake_depth_camera_publisher = grasp_target_fusion.fake_depth_camera_publisher:main",
            "yolo_detection_bridge = grasp_target_fusion.yolo_detection_bridge:main",
            "handeye_sample_collector = grasp_target_fusion.handeye_sample_collector_entry:main",
            "handeye_solver = grasp_target_fusion.handeye_solver_entry:main",
        ],
    },
)
