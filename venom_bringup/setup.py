from setuptools import find_packages, setup
from glob import glob
import os

package_name = 'venom_bringup'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
        (os.path.join('share', package_name, 'rviz_cfg'), glob('rviz_cfg/*.rviz')),
    ],
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
            'imu_odom_publisher = venom_bringup.imu_odom_publisher:main',
        ],
    },
)
