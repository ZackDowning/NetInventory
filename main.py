from gui import InventoryGui, inventory_save_folder_browse
from inventory import InventoryDiscovery, merge_phone_discovery_cucm_export
from parsers import output_to_spreadsheet


def main():
    user_info = InventoryGui()
    if hasattr('user_info', 'password') or hasattr('user_info', 'enable_pw'):
        inventory = InventoryDiscovery(
            user_info.username, user_info.password, user_info.mgmt_ips, user_info.enable_pw, True)
        if hasattr('user_info', 'parsed_cucm_phones'):
            merge_phone_discovery_cucm_export(inventory.phones, user_info.parsed_cucm_phones)
        file_location = inventory_save_folder_browse()
        output_to_spreadsheet(
            inventory.routers_switches, inventory.phones, inventory.waps, inventory.others, inventory.failed_devices,
            file_location)


if __name__ == '__main__':
    main()
