from exceptions import NoPhoneReportFound
import re


class CdpParser:
    def __init__(self, cdp_neighbors, switchports, session):
        self.phones = []
        self.switches = []
        self.waps = []
        self.routers = []
        self.others = []

        def phone_parse(neighbor):
            if neighbor['platform'] == 'IP Phone' or neighbor['capability'].__contains__('Phone'):
                hostname = neighbor['destination_host']
                mgmt_ip = neighbor['management_ip']
                l_intf = neighbor['local_port']
                intf = re.findall(r'.{2}', l_intf)[0] + re.findall(r'\d.+', l_intf)[0]
                macreg = re.findall(r'.{4}', hostname.replace('SEP', ''))
                mac_address = f'{macreg[0]}.{macreg[1]}.{macreg[2]}'.lower()
                voice_vlan = 'None'
                software_version = neighbor['software_version'].replace('.loads', '')
                platform = neighbor['platform']
                for switchport in switchports:
                    if switchport['interface'] == intf:
                        sh_mac_intf = f'show mac address-table interface {intf}'
                        for mac_addr in session.send_command(sh_mac_intf):
                            if mac_addr['vlan'] == switchport['voice_vlan']:
                                voice_vlan = mac_addr['vlan']
                if platform.__contains__('cisco '):
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
            if neighbor['capability'].__contains__('Switch'):
                software_version = neighbor['software_version']
                platform = neighbor['platform']
                for software in neighbor['software_version'].split(','):
                    if software.__contains__('Version'):
                        software_version = software.split('Version')[1]
                        if software_version.__contains__(':'):
                            software_version = software_version.replace(': ', '')
                        else:
                            software_version = software_version.replace(' ', '')
                if platform.__contains__('cisco '):
                    platform = neighbor['platform'].replace('cisco ', '')
                else:
                    platform = neighbor['platform']
                switch = {
                    'hostname': neighbor['destination_host'],
                    'mgmt_ip': neighbor['management_ip'],
                    'local_intf': neighbor['local_port'],
                    'remote_intf': neighbor['remote_port'],
                    'software_version': software_version,
                    'model': platform
                }
                self.switches.append(switch)

        def router_parse(neighbor):
            if neighbor['capability'].__contains__('Router') and \
                    neighbor['capability'].__contains__('Source-Route-Bridge'):
                software_version = neighbor['software_version']
                platform = neighbor['platform']
                for software in neighbor['software_version'].split(','):
                    if software.__contains__('Version'):
                        software_version = software.split('Version')[1]
                        if software_version.__contains__(':'):
                            software_version = software_version.replace(': ', '')
                        else:
                            software_version = software_version.replace(' ', '')
                if platform.__contains__('cisco '):
                    platform = neighbor['platform'].replace('cisco ', '')
                else:
                    platform = neighbor['platform']
                router = {
                    'hostname': neighbor['neighbor'],
                    'mgmt_ip': neighbor['management_ip'],
                    'local_intf': neighbor['local_port'],
                    'remote_intf': neighbor['remote_port'],
                    'software_version': software_version,
                    'model': platform
                }
                self.routers.append(router)

        def wap_parse(neighbor):
            if neighbor['capabilities'].__contains__('Trans-Bridge'):
                software_version = neighbor['software_version']
                platform = neighbor['platform']
                for software in neighbor['software_version'].split(','):
                    if software.__contains__('Version'):
                        software_version = software.split('Version')[1]
                        if software_version.__contains__(':'):
                            software_version = software_version.replace(': ', '')
                        else:
                            software_version = software_version.replace(' ', '')
                if platform.__contains__('cisco '):
                    platform = neighbor['platform'].replace('cisco ', '')
                else:
                    platform = neighbor['platform']
                ap = {
                    'hostname': neighbor['destination_host'],
                    'mgmt_ip': neighbor['management_ip'],
                    'model': platform,
                    'r_intf': neighbor['remote_port'],
                    'l_intf': neighbor['local_port'],
                    'software_version': software_version
                }
                self.waps.append(ap)

        def other_parse(neighbor):
            if not neighbor['capability'].__contains__('Router') and \
                    not neighbor['capability'].__contains__('Source-Route-Bridge') and \
                    not neighbor['capability'].__contains__('Trans-Bridge') and \
                    not neighbor['capability'].__contains__('Switch') and \
                    not neighbor['capability'].__contains__('Phone'):
                other = {
                    'hostname': neighbor['neighbor'],
                    'mgmt_ip': neighbor['management_ip'],
                    'local_intf': neighbor['local_port'],
                    'remote_intf': neighbor['remote_port'],
                    'software_version': neighbor['software_version'],
                    'model': neighbor['platform']
                }
                self.others.append(other)

        for n in cdp_neighbors:
            phone_parse(n)
            switch_parse(n)
            wap_parse(n)
            router_parse(n)
            other_parse(n)


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
