"""
Shared Test Data here
"""

import os
# from tngsdk.benchmark import *
from unittest.mock import Mock
from tngsdk.benchmark.helper import read_yaml

# tng-bench startup arguments
args = [
    "--ped", "path/to/some/pedfile.yml",
    "--generator", "opensourcemano",
    "--config", ".tng-bench.conf",
]
ped_file = os.path.join(os.getcwd(), 'examples-osm/peds/ped_example_vnf.yml')
ped = read_yaml(ped_file)
service_ex = ped['service_experiments']

# ensure that the reference is an absolute path
nsd_pkg_path = os.path.join(os.getcwd(), 'examples-osm/services/example-ns-1vnf-any/example_ns.tar.gz')
vnfd_pkg_path = os.path.join(os.getcwd(), 'examples-osm/services/example-ns-1vnf-any/example_vnf.tar.gz')
func_ex = list()

def simple_function():
    a = 2
    b = 3
    result = 2*3
    print('From simple_function', result)
    return result
