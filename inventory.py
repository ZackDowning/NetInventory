from parsers import CdpParser, cucm_export_parse
from pprint import pp
from net_async import AsyncSessions, BugCheck
import time


def discovery(session):
    cdp_neighbors = session.send_command('show cdp neighbor detail')
    switchports = session.send_command('show interface switchport')
    mac_addrs = session.send_command('show mac address-table')
    cdp_parser = CdpParser(cdp_neighbors, switchports, mac_addrs)
    return {
        'waps': cdp_parser.waps,
        'phones': cdp_parser.phones,
        'switches': cdp_parser.switches,
        'routers': cdp_parser.routers,
        'others': cdp_parser.others
    }


class Compile:
    def __init__(self, sessions_output, known_hostnames):
        inv = sessions_output
        self.new_devices = []
        self.routers_switches = []

        def sw_check(device, device_hostname):
            switches = device['output']['switches']
            for switch in switches:
                sw_hostname = switch['hostname']
                sw_link = {
                    'device': device_hostname,
                    'remote_intf': switch['local_intf'],
                    'local_intf': switch['remote_intf']
                }
                if all(not sw_hostname.__contains__(device['device']['hostname']) for device in inv) and \
                        all(not sw_hostname.__contains__(hostname) for hostname in known_hostnames):
                    new_switch = {
                        'hostname': sw_hostname,
                        'ip_address': switch['mgmt_ip'],
                        'software_version': switch['software_version'],
                        'model': switch['model'],
                        'links': [
                            sw_link
                        ]
                    }
                    if len(self.new_devices) == 0:
                        self.new_devices.append(new_switch)
                    elif all(sw_hostname != n_device['hostname'] for n_device in self.new_devices):
                        self.new_devices.append(new_switch)
                    else:
                        for new_device in self.new_devices:
                            if new_device['hostname'] == sw_hostname:
                                new_device['links'].append(sw_link)
                                break

        def r_check(device, device_hostname):
            routers = device['output']['routers']
            for router in routers:
                r_hostname = router['hostname']
                r_link = {
                    'device': device_hostname,
                    'remote_intf': router['local_intf'],
                    'local_intf': router['remote_intf']
                }
                if all(not r_hostname.__contains__(device['device']['hostname']) for device in inv) and \
                        all(not r_hostname.__contains__(hostname) for hostname in known_hostnames):
                    new_router = {
                        'hostname': r_hostname,
                        'ip_address': router['mgmt_ip'],
                        'software_version': router['software_version'],
                        'model': router['model'],
                        'links': [
                            r_link
                        ]
                    }
                    if len(self.new_devices) == 0:
                        self.new_devices.append(new_router)
                    elif all(r_hostname != n_device['hostname'] for n_device in self.new_devices):
                        self.new_devices.append(new_router)
                    else:
                        for new_device in self.new_devices:
                            if new_device['hostname'] == r_hostname:
                                new_device['links'].append(r_link)
                                break

        for d in inv:
            dev = d['device']
            d_hostname = dev['hostname']
            dev['connection_attempt'] = 'Success'
            self.routers_switches.append(dev)
            sw_check(d, d_hostname)
            r_check(d, d_hostname)


class FullInventory:
    def __init__(self, username, password, initial_mgmt_ips, verbose=False):
        self.routers_switches = []
        self.waps = []
        self.phones = []
        self.others = []
        self.failed_devices = []
        self.new_routers_switches = []
        known_hostnames = []
        init = True
        mgmt_ips = initial_mgmt_ips
        discovery_count = 1

        start_full_discovery_time = time.perf_counter()
        while True:
            start_discovery_time = time.perf_counter()
            if verbose:
                if init:
                    print(f'Starting Initial Discovery on {len(mgmt_ips)} devices...')
                else:
                    print(f'Starting Discovery Pass #{discovery_count} on {len(mgmt_ips)}')
            while True:
                sessions = AsyncSessions(username, password, mgmt_ips, discovery, verbose)
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
                known_hostnames.append(router_switch['hostname'])
                self.routers_switches.append(router_switch)
            new_devices = compiled.new_devices
            if len(new_devices) != 0:
                for new_router_switch in new_devices:
                    known_hostnames.append(new_router_switch['hostname'])
                    new_mgmt_ips.append(new_router_switch['ip_address'])
                    self.new_routers_switches.append(new_router_switch)
                mgmt_ips = new_mgmt_ips
                discovery_count += 1
                finish_discovery_time = time.perf_counter()
                if verbose:
                    discovery_elapsed_time = int(round((finish_discovery_time - start_discovery_time) / 60, 0))
                    if init:
                        print(f'Finished Initial Discovery in {discovery_elapsed_time} minutes')
                    else:
                        print(f'Finished Discovery Pass #{discovery_count} in {discovery_elapsed_time} minutes')
                init = False
            else:
                break
        finish_full_discovery_time = time.perf_counter()
        full_discovery_elapsed_time = int(round((finish_full_discovery_time - start_full_discovery_time) / 60, 0))
        if verbose:
            print(f'Finished Full Discovery in {full_discovery_elapsed_time} minutes')
