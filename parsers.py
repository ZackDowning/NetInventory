from exceptions import NoPhoneReportFound
import re


class CdpParser:
    def __init__(self, cdp_neighbors, switchports, session):
        self.phones = []
        self.switches = []
        self.waps = []

        def phone_parse(neighbor):
            if neighbor['platform'] == 'IP Phone' or neighbor['capability'].__contains__('P'):
                name = neighbor['neighbor']
                x = neighbor['local_interface'].split(' ')
                intf = re.sub(r'\S$', '', x[0]) + x[1]
                macreg = re.findall(r'.{4}', name.replace('SEP', ''))
                mac_address = f'{macreg[0]}.{macreg[1]}.{macreg[2]}'.lower()
                voice_vlan = 'None'
                for switchport in switchports:
                    if switchport['interface'] == intf:
                        sh_mac_intf = f'show mac address-table interface {intf}'
                        for mac_addr in session.send_command(sh_mac_intf):
                            if mac_addr['vlan'] == switchport['voice_vlan']:
                                voice_vlan = mac_addr['vlan']
                phone = {
                    'name': name,
                    'local_intf': intf,
                    'mac_addr': mac_address,
                    'voice_vlan': voice_vlan
                }
                self.phones.append(phone)

        def switch_parse(neighbor):
            if neighbor['capability'].__contains__('S'):
                name1 = neighbor['neighbor']
                x1 = neighbor['local_interface'].split(' ')
                intf1 = re.sub(r'\S$', '', x1[0]) + x1[1]
                y1 = neighbor['neighbor_interface'].split(' ')
                try:
                    r_intf = re.sub(r'\S$', '', y1[0]) + y1[1]
                except IndexError:
                    r_intf = 'Error'
                switch = {
                    'name': name1,
                    'local_intf': intf1,
                    'remote_intf': r_intf
                }
                self.switches.append(switch)

        def wap_parse(neighbor):
            if neighbor['capabilities'].__contains__('Trans-Bridge'):
                software_version = neighbor['software_version']
                for software in neighbor['software_version'].split(','):
                    if software.__contains__('Version'):
                        software_version = software.split('Version')[1]
                        if software_version.__contains__(':'):
                            software_version = software_version.replace(': ', '')
                        else:
                            software_version = software_version.replace(' ', '')
                if neighbor['platform'].__contains__('cisco '):
                    platform = neighbor['platform'].replace('cisco ', '')
                else:
                    platform = neighbor['platform']
                ap = {
                    'hostname': neighbor['destination_host'],
                    'mgmt_ip': neighbor['management_ip'],
                    'platform': platform,
                    'r_intf': neighbor['remote_port'],
                    'l_intf': neighbor['local_port'],
                    'software': software_version
                }
                self.waps.append(ap)

        for n in cdp_neighbors:
            phone_parse(n)
            switch_parse(n)
            wap_parse(n)


def phone_file_parse(file):
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
