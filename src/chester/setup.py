from setuptools import find_packages, setup
from glob import glob  # Import glob function
import os

package_name = 'chester'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob('launch/*.py')),  # Use glob function
        (os.path.join('share', package_name, 'msg'), glob('msg/*.msg')),  # Use glob function
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='emily',
    maintainer_email='emend7@uic.edu',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'image_saver = chester.image_saver:main',
        ],
    },
)