from glob import glob
import os

from setuptools import find_packages, setup


package_name = 'simple_commander_demo'


setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        (
            'share/ament_index/resource_index/packages',
            ['resource/' + package_name],
        ),
        ('share/' + package_name, ['package.xml', 'README.md']),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
        (os.path.join('share', package_name, 'docs'), glob('docs/*.md')),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='venom',
    maintainer_email='liyihan.xyz@gmail.com',
    description='Mock-first waypoint task commander demo for Venom VNV.',
    license='TODO: License declaration',
    extras_require={
        'test': ['pytest'],
    },
    entry_points={
        'console_scripts': [
            'simple_commander_demo = simple_commander_demo.simple_commander:main',
        ],
    },
)
