from .ec2 import EC2
from .cluster import Cluster
from .instance import Instance

from ._version import get_versions
__version__ = get_versions()['version']
del get_versions
