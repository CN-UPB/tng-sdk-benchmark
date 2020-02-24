"""
Shared Test Data here
"""

import os
import pickle
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
service_ex_fpath = os.path.join(os.getcwd(), 'src/tngsdk/benchmark/tests/test_osm_pdriver/fixtures/service_ex.obj')

with open(service_ex_fpath, 'rb') as config_dictionary_file:
    service_ex = pickle.load(config_dictionary_file)
    print(service_ex)

args_fpath = os.path.join(os.getcwd(), 'src/tngsdk/benchmark/tests/test_osm_pdriver/fixtures/args.obj')
with open(args_fpath, 'rb') as config_dictionary_file:
    args_obj = pickle.load(config_dictionary_file)
    print(args_obj)


# ensure that the reference is an absolute path
nsd_pkg_path = os.path.join(os.getcwd(), 'examples-osm/services/example-ns-1vnf-any/example_ns.tar.gz')
vnfd_pkg_path = os.path.join(os.getcwd(), 'examples-osm/services/example-ns-1vnf-any/example_vnf.tar.gz')
func_ex = list()
