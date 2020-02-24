#  Copyright (c) 2018 SONATA-NFV, 5GTANGO, Paderborn University
# ALL RIGHTS RESERVED.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Neither the name of the SONATA-NFV, 5GTANGO, Paderborn University
# nor the names of its contributors may be used to endorse or promote
# products derived from this software without specific prior written
# permission.
#
# This work has been performed in the framework of the SONATA project,
# funded by the European Commission under Grant number 671517 through
# the Horizon 2020 and 5G-PPP programmes. The authors would like to
# acknowledge the contributions of their colleagues of the SONATA
# partner consortium (www.sonata-nfv.eu).
#
# This work has also been performed in the framework of the 5GTANGO project,
# funded by the European Commission under Grant number 761493 through
# the Horizon 2020 and 5G-PPP programmes. The authors would like to
# acknowledge the contributions of their colleagues of the SONATA
# partner consortium (www.5gtango.eu).


import unittest
import logging
from mock import Mock
import shutil
import os
import tngsdk.benchmark.tests.test_osm_pdriver.test_data as TD
from unittest.mock import patch
from tngsdk.benchmark.generator.osm \
    import OSMServiceConfigurationGenerator

"""
Use args from TC1
"""

"""
@nsd_pkg_path - '/home/avi/tng-sdk-benchmark/examples-osm/peds/\
    ../services/example-ns-1vnf-any/example_ns.tar.gz'
@vnfd_pkg_path - '/home/avi/tng-sdk-benchmark/examples-osm/peds/\
    ../services/example-ns-1vnf-any/example_vnf.tar.gz'
@func_ex -
@service_ex - service experiment configuration object
"""


class TestOSMServiceConfigurationGenerator(unittest.TestCase):
    """
    Test OSMServiceConfigurationGenerator
    src/tngsdk/benchmark/generator/osm.py
    """

    @classmethod
    def setUpClass(cls):
        """
        cp fixture to tmp
        """
        file = 'src/tngsdk/benchmark/tests/test_osm_pdriver/fixtures/example_vnf_00000_vnfd.tar.gz'
        source = os.path.join(os.getcwd(), file)
        destination = "/tmp/tmp3c4i29uk/example_vnf_00000_vnfd.tar.gz"
        os.system("echo 'pg@upb123' | sudo -S mkdir /tmp/tmp3c4i29uk/")
        shutil.copyfile(source, destination)
        print('file copied to /tmp location')

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_constructor_instantiation_without_args(self):
        """
        Test if exception is raised when class is instantiated with false arguments
        """
        with self.assertRaises(TypeError) as cm:
            OSMServiceConfigurationGenerator()
        self.assertRegex(cm.exception.args[0], 'args', msg='did not match expected input arguments')

    def test_constructor_instantiation_with_args(self):
        """
        """
        actual = OSMServiceConfigurationGenerator(TD.args)
        print(actual)
        self.assertTrue('args' in actual.__dict__)

    def test_generate_without_args(self):
        """
        """
        expected = "missing 4 required positional arguments"
        actual = OSMServiceConfigurationGenerator(TD.args)
        with self.assertRaises(TypeError) as cm:
            gen = actual.generate()
            print(gen)
        self.assertRegex(cm.exception.args[0], expected, msg='did not match expected input arguments')

    def test_generator_with_4_args(self):
        """
        """
        osm = OSMServiceConfigurationGenerator(TD.args_obj)
        # with self.assertRaises(TypeError) as cm:
        actual = osm.generate(
            TD.nsd_pkg_path,
            TD.vnfd_pkg_path,
            TD.func_ex,
            TD.service_ex,
        )
        print(actual)
        # self.assertRegex(cm.exception.args[0], expected, msg='did not match expected input arguments')
        # with self.assertRaises(SomeException):
        # print(actual)
