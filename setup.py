from __future__ import print_function, division, absolute_import

from distutils.core import setup
from setuptools import find_packages

import versioneer

setup(name='dec2',
      version=versioneer.get_version(),
      cmdclass=versioneer.get_cmdclass(),
      description='dec2',
      long_description='',
      author='Daniel Rodriguez',
      url='https://github.com/dask/dec2',
      license='Apache 2.0',
      packages=find_packages(),
      include_package_data=True,
      entry_points="""
        [console_scripts]
        dec2=dec2.cli:start
      """,
      install_requires=["click", "paramiko", "boto3", "pyyaml", "salt-pepper", "cm-api"]
)
