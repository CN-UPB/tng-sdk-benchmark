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


import tngsdk.benchmark.tests.test_osm_pdriver.test_data as TD
import unittest
from tngsdk.benchmark import main
from tngsdk.benchmark import parse_args
# log = logging.getLogger("TestLog")


class TestCmdLineArgs(unittest.TestCase):
    """Test if command line arguments are updating or not"""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_generator_and_config_args(self):
        """Are cmdline args getting added to args object"""
        # Namespace object
        actual = parse_args(TD.args)
        msg1 = '{} <> {}'.format(actual.service_generator, TD.args[3])
        self.assertEqual(actual.service_generator, TD.args[3], msg=msg1)
        msg2 = '{} <> {}'.format(actual.configfile, TD.args[5])
        self.assertEqual(actual.configfile, TD.args[5], msg=msg2)
        msg3 = '{} <> {}'.format(actual.ped, TD.args[1])
        self.assertEqual(actual.ped, TD.args[1], msg=msg3)
