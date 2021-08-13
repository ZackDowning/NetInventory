from exceptions import NoPhoneReportFound
from net_async import multithread
import re


class CdpParser:
    def __init__(self, cdp_neighbors, switchports, session):
        nxos = False
        try:
            _ = cdp_neighbors[0]['destination_host']
            hostname_s = 'destination_host'
            version_s = 'software_version'
            mgmt_ip_s = 'management_ip'
        except KeyError:
            nxos = True
            hostname_s = 'destination_host'
            version_s = 'software_version'
            mgmt_ip_s = 'mgmt_ip'
        self.phones = []
        self.switches = []
        self.waps = []
        self.routers = []
        self.others = []

        def phone_parse(neighbor):
            mgmt_ip = neighbor[mgmt_ip_s]
            hostname = neighbor[hostname_s].split('.')[0]
            if nxos:
                sysname = neighbor['sysname']
                if sysname != '':
                    hostname = sysname
                if mgmt_ip == '':
                    mgmt_ip = neighbor['interface_ip']
            l_intf = neighbor['local_port']
            intf = re.findall(r'.{2}', l_intf)[0] + re.findall(r'\d.+', l_intf)[0]
            macreg = re.findall(r'.{4}', hostname.replace('SEP', ''))
            mac_address = f'{macreg[0]}.{macreg[1]}.{macreg[2]}'.lower()
            voice_vlan = 'None'
            software_version = neighbor[version_s].replace('.loads', '')
            platform = neighbor['platform']
            for switchport in switchports:
                if switchport['interface'] == intf:
                    sh_mac_intf = f'show mac address-table interface {intf}'
                    for mac_addr in session.send_command(sh_mac_intf):
                        if mac_addr['vlan'] == switchport['voice_vlan']:
                            voice_vlan = mac_addr['vlan']
                            break
                    break
            if platform.__contains__('Cisco IP Phone'):
                platform = neighbor['platform'].replace('Cisco IP Phone ', '')
            else:
                platform = neighbor['platform']
            phone = {
                'hostname': hostname,
                'local_intf': l_intf,
                'mgmt_ip': mgmt_ip,
                'mac_addr': mac_address,
                'voice_vlan': voice_vlan,
                'software_version': software_version,
                'model': platform
            }
            self.phones.append(phone)

        def switch_parse(neighbor):
            mgmt_ip = neighbor[mgmt_ip_s]
            hostname = neighbor[hostname_s].split('.')[0]
            if nxos:
                sysname = neighbor['sysname']
                if sysname != '':
                    hostname = sysname
                if mgmt_ip == '':
                    mgmt_ip = neighbor['interface_ip']
            software_version = neighbor[version_s]
            platform = neighbor['platform']
            for software in software_version.split(','):
                if software.__contains__('Version'):
                    software_version = software.split('Version')[1].split('REL')[0]
                    if software_version.__contains__(':'):
                        software_version = software_version.replace(': ', '')
                    else:
                        software_version = software_version.replace(' ', '')
                    break
            if platform.__contains__('cisco '):
                platform = neighbor['platform'].replace('cisco ', '')
            elif platform.__contains__('Cisco '):
                platform = neighbor['platform'].replace('Cisco ', '')
            else:
                platform = neighbor['platform']
            switch = {
                'hostname': hostname,
                'mgmt_ip': mgmt_ip,
                'local_intf': neighbor['local_port'],
                'remote_intf': neighbor['remote_port'],
                'software_version': software_version,
                'model': platform
            }
            self.switches.append(switch)

        def router_parse(neighbor):
            mgmt_ip = neighbor[mgmt_ip_s]
            hostname = neighbor[hostname_s].split('.')[0]
            if nxos:
                sysname = neighbor['sysname']
                if sysname != '':
                    hostname = sysname
                if mgmt_ip == '':
                    mgmt_ip = neighbor['interface_ip']
            software_version = neighbor[version_s]
            platform = neighbor['platform']
            for software in software_version.split(','):
                if software.__contains__('Version'):
                    software_version = software.split('Version')[1]
                    if software_version.__contains__(':'):
                        software_version = software_version.replace(': ', '')
                    else:
                        software_version = software_version.replace(' ', '')
                    break
            if platform.__contains__('cisco '):
                platform = neighbor['platform'].replace('cisco ', '')
            elif platform.__contains__('Cisco '):
                platform = neighbor['platform'].replace('Cisco ', '')
            else:
                platform = neighbor['platform']
            router = {
                'hostname': hostname,
                'mgmt_ip': mgmt_ip,
                'local_intf': neighbor['local_port'],
                'remote_intf': neighbor['remote_port'],
                'software_version': software_version,
                'model': platform
            }
            self.routers.append(router)

        def wap_parse(neighbor):
            mgmt_ip = neighbor[mgmt_ip_s]
            hostname = neighbor[hostname_s].split('.')[0]
            if nxos:
                sysname = neighbor['sysname']
                if sysname != '':
                    hostname = sysname
                if mgmt_ip == '':
                    mgmt_ip = neighbor['interface_ip']
            software_version = neighbor[version_s]
            platform = neighbor['platform']
            for software in software_version.split(','):
                if software.__contains__('Version'):
                    software_version = software.split('Version')[1]
                    if software_version.__contains__(':'):
                        software_version = software_version.replace(': ', '')
                    else:
                        software_version = software_version.replace(' ', '')
                    break
            if platform.__contains__('cisco '):
                platform = neighbor['platform'].replace('cisco ', '')
            elif platform.__contains__('Cisco '):
                platform = neighbor['platform'].replace('Cisco ', '')
            else:
                platform = neighbor['platform']
            ap = {
                'hostname': hostname,
                'mgmt_ip': mgmt_ip,
                'model': platform,
                'r_intf': neighbor['remote_port'],
                'l_intf': neighbor['local_port'],
                'software_version': software_version
            }
            self.waps.append(ap)

        def other_parse(neighbor):
            mgmt_ip = neighbor[mgmt_ip_s]
            hostname = neighbor[hostname_s].split('.')[0]
            if nxos:
                sysname = neighbor['sysname']
                if sysname != '':
                    hostname = sysname
                if mgmt_ip == '':
                    mgmt_ip = neighbor['interface_ip']
            other = {
                'hostname': hostname,
                'mgmt_ip': mgmt_ip,
                'local_intf': neighbor['local_port'],
                'remote_intf': neighbor['remote_port'],
                'software_version': neighbor[version_s],
                'model': neighbor['platform']
            }
            self.others.append(other)

        def parse(n):
            capabilities = n['capabilities']
            if n['platform'].__contains__('IP Phone') or capabilities.__contains__('Phone'):
                phone_parse(n)
            elif capabilities.__contains__('Switch'):
                switch_parse(n)
            elif capabilities.__contains__('Trans-Bridge'):
                wap_parse(n)
            elif capabilities.__contains__('Router') and capabilities.__contains__('Source-Route-Bridge'):
                router_parse(n)
            else:
                other_parse(n)

        multithread(parse, cdp_neighbors)


def cucm_export_parse(file):
    phones = {}
    while True:
        try:
            with open(file) as phonelist_csv:
                for line in phonelist_csv:
                    if line.__contains__('Description,Device Name,Directory Number 1'):
                        pass
                    else:
                        info = line.split(',')
                        device_name = info[1]
                        description = info[0]
                        directory_number = info[2]
                        phones[device_name.upper()] = {
                            'description': description,
                            'directory_number': directory_number
                        }
            break
        except FileNotFoundError:
            raise NoPhoneReportFound('No phone report file found at provided location.')
    return phones
