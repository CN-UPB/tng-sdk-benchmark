#  Copyright (c) 2019 SONATA-NFV, 5GTANGO, Paderborn University
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
from tngsdk.benchmark.pdriver.osm.conn_mgr import OSMConnectionManager
from tngsdk.benchmark.logger import TangoLogger
from tngsdk.benchmark.helper import parse_ec_parameter_key, write_json
from tngsdk.benchmark.helper import write_yaml

import paramiko
import time
import os
import stat
import scp
import datetime
LOG = TangoLogger.getLogger(__name__)

PATH_SHARE = "tngbench_share"
PATH_CMD_START_LOG = "cmd_start.log"
PATH_CMD_STOP_LOG = "cmd_stop.log"
WAIT_PADDING_TIME = 3  # FIXME extra time to wait (to have some buffer)
PATH_EXPERIMENT_TIMES = "experiment_times.json"
MAX_RETRIES = 10


class OsmDriver(object):
    """
    PDRIVER Class to allow connection to Open Source MANO (OSM)
    """

    def __init__(self, args, config):

        self.args = args
        self.config = config
        self.conn_mgr = OSMConnectionManager(self.config)
        self.t_experiment_start = None
        self.t_experiment_stop = None
        # self.conn_mgr.connect()
        if self.conn_mgr.connect():
            LOG.info("Connection to OSM Established.")
        else:
            LOG.error('Connection to OSM Failed!')
            raise Exception()

    def setup_platform(self):
        pass
        # vim_access={}
        # vim_access['vim-type'] = "openstack"
        # vim_access['description'] = "description"
        # vim_access['vim-url'] = "http://fgcn-backflip9.cs.upb.de/identity/v3"
        # vim_access['vim-username'] = "admin"
        # vim_access['vim-password'] = "admin"
        # vim_access['vim-tenant-name'] = "admin"

        # vim_config = {"use_floating_ip":True}
        # write_yaml('/tmp/temp_vim_config.yaml', vim_config)
        # vim_access['config'] = open(r'/tmp/temp_vim_config.yaml')
        # try:
        #     self.conn_mgr.client.vim.create("openstack-site", vim_access, wait=True)
        # except Exception:
        #     pass

    def setup_experiment(self, ec):

        # Reset main vnf IP addresses
        self.main_vm_data_ip_1 = None
        self.main_vm_data_ip_2 = None

        # Uplaod VNFD package
        try:
            self.vnfd_id = self.conn_mgr.upload_vnfd_package(ec.vnfd_package_path)
            self.probe_vnfd_id = []
            for probe_path in ec.probe_package_paths:
                self.probe_vnfd_id.append(self.conn_mgr.upload_vnfd_package(probe_path))
            self.nsd_id = self.conn_mgr.upload_nsd_package(ec.nsd_package_path)
            self.nsi_uuid = (self.conn_mgr.get_nsd(ec.experiment.name).get('_id'))
        except:
            LOG.error("Could not Upload NSD and VNFD for experiment {}. "
                      "Skipping this experiment.".format(ec.experiment.name))

        # Instantiate the NSD
        try:
            self.conn_mgr.create_ns(self.nsi_uuid, ec.name, self.config.get('VIM_name'), wait=True)
        except:
            LOG.error("Could not create NS Instance.")
        else:
            LOG.info("Instantiated service: {}".format(self.nsi_uuid))

        # Fetch IP Addresses of the deployed instances
        self._get_ip_addresses(ec)

    def _get_ip_addresses(self, ec):
        self.ip_addresses = {}
        try:
            ns = self.conn_mgr.get_ns(ec.name)
            # fetch all VNFs from NS
            for vnf_ref in ns.get('constituent-vnfr-ref'):
                vnf_desc = self.conn_mgr.get_vnf(vnf_ref)
                # fetch all  VDUs from a VNF
                for vdur in vnf_desc.get('vdur'):
                    self.ip_addresses[vdur.get('vdu-id-ref')] = {}
                    # fetch all interfaces for this VDU
                    for interfaces in vdur.get('interfaces'):
                        if interfaces.get('mgmt-vnf') is None:  # if it is not the management interface
                            if not vdur.get('vdu-id-ref').startswith('mp.'):  # if it is the main VNF
                                if self.main_vm_data_ip_1 is None:
                                    self.main_vm_data_ip_1 = interfaces.get('ip-address')
                                else:
                                    self.main_vm_data_ip_2 = interfaces.get('ip-address')
                            if "data1" in interfaces.get("name"):  # if it is "eth0-data1"
                                self.ip_addresses[vdur.get('vdu-id-ref')]['data1'] = interfaces.get('ip-address')
                            elif "data2" in interfaces.get("name"):  # if it is "eth0-data2"
                                self.ip_addresses[vdur.get('vdu-id-ref')]['data2'] = interfaces.get('ip-address')
                            else:  # else it is "eth0-data"
                                self.ip_addresses[vdur.get('vdu-id-ref')]['data'] = interfaces.get('ip-address')
                        else:
                            self.ip_addresses[vdur.get('vdu-id-ref')]['mgmt'] = interfaces.get('ip-address')
        except Exception:
            LOG.error("Could not fetch IP addresses.")

    def execute_experiment(self, ec):

        """
        Execute the experiment
        """
        skip_experiment = False
        self.ssh_clients = {}
        vnf_username = self.config.get('main_vm_username')
        vnf_password = self.config.get('main_vm_password')
        probe_username = self.config.get('probe_username')
        probe_password = self.config.get('probe_password')

        # Renew connection to prevent OSM Client connection from expiring
        self.conn_mgr.connect()

        login_uname = None
        login_pass = None
        # Begin executing commands
        time_warmup = int(ec.parameter['ep::header::all::time_warmup'])
        LOG.debug(f'Warmup time: Sleeping for {time_warmup}')
        time.sleep(time_warmup)
        global PATH_SHARE
        PATH_SHARE = os.path.join('/', PATH_SHARE)
        # TODO: Modularize this and remove the for loop.
        for ex_p in ec.experiment.experiment_parameters:
            cmd_start = ex_p['cmd_start']
            # LIMITATION: This assumes cmd_start is a bash script.
            cmd_start += f" vnf {self.main_vm_data_ip_1}"
            for fn, fn_info in self.ip_addresses.items():
                if fn.startswith("mp."):
                    cmd_start += f" {fn} {fn_info['data']}"

            function = ex_p['function']

            if function.startswith('mp.'):
                login_uname = probe_username
                login_pass = probe_password
            else:
                login_uname = vnf_username
                login_pass = vnf_password

            LOG.info(f"Connecting SSH to {function} at IP:{self.ip_addresses[function]['mgmt']}")
            timeout = time.time() + 15 * 60  # in seconds
            while not self._ssh_connect(function, self.ip_addresses[function]['mgmt'], username=login_uname,
                                        password=login_pass):
                # Keep looping until a connection is established
                time.sleep(15)
                if time.time() > timeout:
                    LOG.error("Connection timed out: Could not connect using ssh. Skipping experiment")
                    skip_experiment = True
                continue
            if not skip_experiment:
                try:
                    LOG.info(f'Creating {PATH_SHARE} folder at {function}')
                    stdin, stdout, stderr = self.ssh_clients[function].exec_command(
                        f'sudo mkdir {PATH_SHARE}')
                    time.sleep(3)
                    stdin, stdout, stderr = self.ssh_clients[function].exec_command(
                        f'sudo chmod 777 {PATH_SHARE}')
                    time.sleep(3)
                    if "input" in function:
                        stdin, stdout, stderr = self.ssh_clients[function].exec_command(
                            f'sudo ip route add {self.config.get("data_2_subnet")} via {self.main_vm_data_ip_1}')
                    elif "output" in function:
                        stdin, stdout, stderr = self.ssh_clients[function].exec_command(
                            f'sudo ip route add {self.config.get("data_1_subnet")} via {self.main_vm_data_ip_2}')
                    else:
                        stdin, stdout, stderr = self.ssh_clients[function].exec_command(
                            f'sudo sysctl -w net.ipv4.ip_forward=1')
                    time.sleep(3)
                    LOG.info(f"Executing start command {cmd_start} at {function}")
                    stdin, stdout, stderr = self.ssh_clients[function].exec_command(
                        f'cd / ; sudo sh -c \'{cmd_start}\' &> {PATH_SHARE}/{PATH_CMD_START_LOG} &')
                except:
                    LOG.error("Exception caught during execution of experiment. Skipping experiment.")

    def _ssh_connect(self, function_name, ip_address, username, password):
        """
        Connect to SSH server of `function_name` at `ip_address` using `username` and `password`
        TODO: Handle paramiko level logs, remove unwanted error log messages.
        """
        try:
            self.ssh_clients[function_name] = paramiko.SSHClient()
            self.ssh_clients[function_name].set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh_clients[function_name].connect(ip_address, username=username,
                                                    password=password, look_for_keys=False)
        except:  # Have to use bare except here due to the several exceptions that can happen here.
            return False
        else:
            return True

    def teardown_experiment(self, ec):
        """
        Execute stop commands at VMs and collect logs
        """

        # Sleep for experiment duration
        # experiment_duration = int(ec.parameter['ep::header::all::time_limit'])
        # LOG.info(f'Experiment duration: Sleeping for {experiment_duration} seconds before stopping')
        self.t_experiment_start = datetime.datetime.now()
        self._wait_experiment(ec)
        self.t_experiment_stop = datetime.datetime.now()
        # time.sleep(experiment_duration)

        # hold execution for manual debugging:
        if self.args.hold_and_wait_for_user:
            input("Press Enter to continue...")
        for i in range(MAX_RETRIES):
            try:
                for ex_p in ec.experiment.experiment_parameters:
                    cmd_stop = ex_p['cmd_stop']
                    function = ex_p['function']
                    # self.ssh_clients[function] = paramiko.SSHClient()
                    # self.ssh_clients[function].set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    LOG.info(f"Executing stop command {cmd_stop}")
                    stdin, stdout, stderr = self.ssh_clients[function].exec_command(
                        f'cd / ; sudo sh -c \'{cmd_stop}\' &> {PATH_SHARE}/{PATH_CMD_STOP_LOG} &')
                    self._collect_experiment_results(ec, function)
                    LOG.info(stdout)
                    LOG.info(f'Closing SSH Connection to {function}')
                    # Close the SSH connection to prevent any possible memory leaks from paramiko
                    self.ssh_clients[function].close()
                    # Delete the SSH object all together
                    del self.ssh_clients[function]
            except:
                LOG.error("Exception caught during the execution of cmd_stop. Trying again.")
            else:
                break
        self.conn_mgr.client.ns.delete(ec.name, wait=True)
        LOG.info("Deleted Service: {}".format(self.nsi_uuid))
        self.conn_mgr.client.nsd.delete(self.nsd_id)
        LOG.info("Deleted NSD: {}".format(self.nsd_id))
        self.conn_mgr.client.vnfd.delete(self.vnfd_id)
        LOG.info("Deleted VNFD: {}".format(self.vnfd_id))
        for probe_vnfd_id_i in self.probe_vnfd_id:
            self.conn_mgr.client.vnfd.delete(probe_vnfd_id_i)
            LOG.info("Deleted Probe VNFD: {}".format(probe_vnfd_id_i))

    def teardown_platform(self):
        # self.conn_mgr.client.vim.delete("trial_vim")
        pass

    def instantiate_service(self, uuid):
        pass

    def _store_times(self, path):
        data = {
            "experiment_start": str(self.t_experiment_start),
            "experiment_stop": str(self.t_experiment_stop)
        }
        try:
            LOG.debug("Writing timing data to: {}".format(path))
            write_json(path, data)
        except BaseException as ex:
            LOG.error("Could not write to {}: {}".format(path, ex))

    def _collect_experiment_results(self, ec, function):
        """
        SCP into `function` and collect `PATH_SHARE` folder
        """
        LOG.info(f"Collecting experiment results from {function}")
        remote_dir = f'{PATH_SHARE}/'
        # generate result paths
        dst_path = os.path.join(self.args.result_dir, ec.name)
        # Replace function name and prepend 'osm.' to make sure result directories are unique
        function_path = f'osm.{function}'
        # for each vm collect files from containers
        function_dst_path = os.path.join(dst_path, function_path)
        os.makedirs(function_dst_path, exist_ok=True)
        time.sleep(3)
        local_dir = f'{function_dst_path}/'
        for i in range(MAX_RETRIES):
            try:
                scp_client = scp.SCPClient(self.ssh_clients[function].get_transport())
                scp_client.get(remote_dir, local_dir, recursive=True)
            except:
                LOG.error("Exception caught while copying the results. Trying again.")
                continue
            else:
                break
        self._store_times(
            os.path.join(dst_path, PATH_EXPERIMENT_TIMES))

    def _experiment_wait_time(self, ec):
        time_limit = int(ec.parameter.get("ep::header::all::time_limit", 0))
        if time_limit < 1:
            return time_limit
        time_limit += WAIT_PADDING_TIME
        return time_limit

    def _wait_experiment(self, ec, text="Running experiment"):
        time_limit = self._experiment_wait_time(ec)
        if time_limit < 1:
            return  # we don't need to wait
        self._wait_time(time_limit, "{} '{}'".format(text, ec))

    def _wait_time(self, time_limit, text="Wait"):
        WAIT_NUMBER_OF_OUTPUTS = 10  # FIXME make configurable
        if time_limit < 1:
            return  # we don't need to wait
        time_slot = int(time_limit / WAIT_NUMBER_OF_OUTPUTS)
        # wait and print status
        for i in range(0, WAIT_NUMBER_OF_OUTPUTS):
            time.sleep(time_slot)
            LOG.debug("{}\t... {}%"
                      .format(text, (100 / WAIT_NUMBER_OF_OUTPUTS) * (i + 1)))
