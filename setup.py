from __future__ import print_function, division, absolute_import

import os
import versioneer
from setuptools import setup, find_packages

# Add formulas and templates to the package
formulas_dir = os.path.join('dec2', 'formulas')
all_directories = [[os.path.join(d, f) for f in folders]
                   for d, folders, files in os.walk(formulas_dir)]
flattern = [item for sublist in all_directories for item in sublist]
formulas_data = [folder[len('dec2/'):] + '/*' for folder in flattern]
package_data = formulas_data + ["templates/*"]

packages = find_packages()
packages.append("dec2.tests")

setup(name='dec2',
      version=versioneer.get_version(),
      cmdclass=versioneer.get_cmdclass(),
      description='dec2',
      long_description='',
      author='Daniel Rodriguez',
      url='https://github.com/dask/dec2',
      license='Apache 2.0',
      packages=packages,
      include_package_data=True,
      package_data={'dec2': package_data},
      entry_points="""
        [console_scripts]
        dec2=dec2.cli.main:start
      """,
      install_requires=["six", "click", "paramiko", "boto3", "pyyaml", "salt-pepper"])
