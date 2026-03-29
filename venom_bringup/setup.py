from setuptools import find_packages, setup
from glob import glob
import os

package_name = 'venom_bringup'

def collect_config_data_files():
    config_root = 'config'
    data_files = []
    for root, _, _ in os.walk(config_root):
        yaml_files = glob(os.path.join(root, '*.yaml'))
        json_files = glob(os.path.join(root, '*.json'))
        files = yaml_files + json_files
        if not files:
            continue
        rel_root = os.path.relpath(root, config_root)
        install_dir = os.path.join('share', package_name, 'config')
        if rel_root != '.':
            install_dir = os.path.join(install_dir, rel_root)
        data_files.append((install_dir, files))
    return data_files


def collect_launch_data_files():
    launch_root = 'launch'
    data_files = []
    for root, _, _ in os.walk(launch_root):
        py_files = glob(os.path.join(root, '*.py'))
        if not py_files:
            continue
        rel_root = os.path.relpath(root, launch_root)
        install_dir = os.path.join('share', package_name, 'launch')
        if rel_root != '.':
            install_dir = os.path.join(install_dir, rel_root)
        data_files.append((install_dir, py_files))
    return data_files


setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'rviz_cfg'), glob('rviz_cfg/*.rviz')),
    ] + collect_launch_data_files() + collect_config_data_files(),
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='venom',
    maintainer_email='liyihan.xyz@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'multi_waypoint_commander = '
            'venom_bringup.multi_waypoint_commander:main',
        ],
    },
)
