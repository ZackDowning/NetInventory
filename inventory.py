from parsers import CdpParser, cucm_export_parse
from pprint import pp
from net_async import AsyncSessions, BugCheck
import time


def discovery(session):
    cdp_neighbors = session.send_command('show cdp neighbor detail')
    switchports = session.send_command('show interface switchport')
    mac_addrs = session.send_command('show mac address-table')
    cdp_parser = CdpParser(cdp_neighbors, switchports, mac_addrs, session)
    return {
        'waps': cdp_parser.waps,
        'phones': cdp_parser.phones,
        'routers_switches': cdp_parser.routers_switches,
        'others': cdp_parser.others
    }


class Compile:
    def __init__(self, sessions_output, known_hostnames):
        inv = sessions_output
        self.new_devices = []
        self.routers_switches = []

        def check(routers_switches_raw, neighbor_device):
            for rw_sw in routers_switches_raw:
                hostname = rw_sw['hostname']
                neighbor = {
                    'hostname': neighbor_device['hostname'],
                    'ip_address': neighbor_device['ip_address'],
                    'remote_intf': rw_sw['local_intf'],
                    'local_intf': rw_sw['remote_intf']
                }
                if all(not hostname.__contains__(device['device']['hostname']) for device in inv) and \
                        all(not hostname.__contains__(known_hostname) for known_hostname in known_hostnames):
                    new_router = {
                        'hostname': hostname,
                        'ip_address': rw_sw['mgmt_ip'],
                        'software_version': rw_sw['software_version'],
                        'model': rw_sw['model'],
                        'neighbors': [
                            neighbor
                        ]
                    }
                    if len(self.new_devices) == 0:
                        self.new_devices.append(new_router)
                    elif all(hostname != n_device['hostname'] for n_device in self.new_devices):
                        self.new_devices.append(new_router)
                    else:
                        for new_device in self.new_devices:
                            if new_device['hostname'] == hostname:
                                new_device['links'].append(neighbor)
                                break

        for output in inv:
            root_device = output['device']
            routers_switches_list = output['output']['routers_switches']
            root_device['connection_attempt'] = 'Success'
            self.routers_switches.append(root_device)
            check(routers_switches_list, root_device)


class FullInventory:
    def __init__(self, username, password, initial_mgmt_ips, enable_pw='', verbose=False, recursive=True):
        self.routers_switches = []
        self.waps = []
        self.phones = []
        self.others = []
        self.failed_devices = []
        new_routers_switches = []
        known_hostnames = []
        init = True
        mgmt_ips = initial_mgmt_ips
        discovery_count = 1

        start_full_discovery_time = time.perf_counter()
        while True:
            start_discovery_time = time.perf_counter()
            if verbose:
                if init:
                    print(f'Starting Initial Discovery on {len(mgmt_ips)} Devices...')
                else:
                    print(f'Starting Discovery Pass #{discovery_count} on {len(mgmt_ips)} Devices...')
            while True:
                sessions = AsyncSessions(username, password, mgmt_ips, discovery, enable_pw, True)
                bug_check = BugCheck(sessions.successful_devices, sessions.failed_devices, mgmt_ips)
                if not bug_check.bug:
                    break
                else:
                    if verbose:
                        print('Bug Found')

            failed_devices = sessions.failed_devices
            if len(failed_devices) != 0:
                for failed_device in failed_devices:
                    if init:
                        failed_device['discovery_status'] = 'existing'
                    else:
                        failed_device['discovery_status'] = 'new'
                    self.failed_devices.append(failed_device)

            sessions_outputs = sessions.outputs
            for output in sessions_outputs:
                output = output['output']
                for wap in output['waps']:
                    self.waps.append(wap)
                for phone in output['phones']:
                    self.phones.append(phone)
                for other in output['others']:
                    self.others.append(other)

            new_mgmt_ips = []
            compiled = Compile(sessions_outputs, known_hostnames)
            for router_switch in compiled.routers_switches:
                if init:
                    router_switch['discovery_status'] = 'existing'
                else:
                    router_switch['discovery_status'] = 'new'
                router_switch['connection_attempt'] = 'Success'
                known_hostnames.append(router_switch['hostname'])
                self.routers_switches.append(router_switch)
                for new_router_switch in new_routers_switches:
                    if router_switch['ip_address'] == new_router_switch['ip_address']:
                        new_routers_switches.remove(new_router_switch)
                        break
            new_devices = compiled.new_devices
            finish_discovery_time = time.perf_counter()
            if verbose:
                discovery_elapsed_time = int(round((finish_discovery_time - start_discovery_time) / 60, 0))
                if init:
                    if recursive:
                        print(f'Finished Initial Discovery in {discovery_elapsed_time} Minutes')
                else:
                    print(f'Finished Discovery Pass #{discovery_count} in {discovery_elapsed_time} Minutes')
            if len(new_devices) != 0:
                for new_router_switch in new_devices:
                    known_hostnames.append(new_router_switch['hostname'])
                    new_mgmt_ips.append(new_router_switch['ip_address'])
                    new_routers_switches.append(new_router_switch)
                mgmt_ips = new_mgmt_ips
                discovery_count += 1
                init = False
                if not recursive:
                    break
            else:
                break

        for new_router_switch in new_routers_switches:
            new_router_switch['discovery_status'] = 'new'
            new_router_switch['connection_attempt'] = 'Failed'
            self.routers_switches.append(new_router_switch)
        finish_full_discovery_time = time.perf_counter()
        full_discovery_elapsed_time = int(round((finish_full_discovery_time - start_full_discovery_time) / 60, 0))
        if verbose:
            print(f'Finished Full Discovery in {full_discovery_elapsed_time} minutes')
