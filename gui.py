import PySimpleGUI as Sg
from net_async import MgmtIPAddresses
from parsers import cucm_export_parse
from exceptions import NoPhoneReportFound
from os import path

f = {
    'font': 'Helvetica',
    'size': {
        'small': '12',
        'medium': '14',
        'large': '16'
    }}
s_font = f'{f["font"]} {f["size"]["small"]}'
m_font = f'{f["font"]} {f["size"]["medium"]}'
l_font = f'{f["font"]} {f["size"]["large"]}'
window_title = 'NetInventory'


def gui_print(string, font=m_font):
    return [Sg.Text(str(string), font=font)]


def gui_print_box(string, font=m_font, size=(20, 100)):
    return [Sg.Multiline(str(string), font=font, size=size)]


def gui_checkbox(string, key=None, font=m_font, size=(20, 100)):
    return [Sg.Checkbox(str(string), font=font, size=size, key=key)]


def button(string, font=m_font):
    return [Sg.Button(str(string), font=font, bind_return_key=True)]


def dropdown(input_list, font=m_font):
    return [Sg.Combo(input_list, font=font, bind_return_key=True)]


def file_browse_botton(string, font=m_font):
    return [
        Sg.Input(Sg.user_settings_get_entry('-filename-', ''), key='file'),
        Sg.FileBrowse(str(string), initial_folder='./', font=font)]


def folder_browse_botton(string, font=m_font):
    return [
        Sg.Input(Sg.user_settings_get_entry('-folder-', ''), key='folder'),
        Sg.FolderBrowse(str(string), initial_folder='./', font=font)]


def cucm_file_browse_botton(string, font=m_font):
    return [
        Sg.Input(Sg.user_settings_get_entry('-cucm_file-', ''), key='cucm_file'),
        Sg.FileBrowse(str(string), initial_folder='./', font=font)]


def gui_user_input(font=m_font):
    return [Sg.Input(Sg.user_settings_get_entry('-username-', ''), key='user', font=font)]


def gui_password_input(default_string='', font=m_font):
    return [Sg.InputText(str(default_string), key='pass', password_char='*', font=font)]


def gui_enable_password_input(default_string='', font=m_font):
    return [Sg.InputText(str(default_string), key='enable_pw', password_char='*', font=font)]


def w_mgmt_file_main(current_window=None):
    """Main / Home Window"""
    if current_window is not None:
        current_window.close()
    layout = [
        gui_print('Select file containing device management IP addresses'),
        file_browse_botton('Browse'),
        gui_checkbox('Use CUCM Export', key='cucm_export'),
        button('Next')
    ]
    return Sg.Window(window_title, layout, margins=(100, 100))


def w_save_folder(current_window=None):
    """Folder Save Window"""
    if current_window is not None:
        current_window.close()
    layout = [
        gui_print('Select folder to save Inventory Export'),
        folder_browse_botton('Browse'),
        button('Save File')
    ]
    return Sg.Window(window_title, layout, margins=(100, 100))


def w_credential(current_window=None):
    """Get Network Credential Window"""
    if current_window is not None:
        current_window.close()
    layout = [
        gui_print('Network Username'),
        gui_user_input(),
        gui_print('Network Password'),
        gui_password_input(''),
        gui_print('Enable Password(If Applicable)'),
        gui_enable_password_input(''),
        button('Run Inventory Discovery')
    ]
    return Sg.Window(window_title, layout, margins=(100, 100))


def w_cucm_file_main(current_window=None):
    """Window for CUCM export file selection"""
    if current_window is not None:
        current_window.close()
    layout = [
        gui_print('Select CUCM export CSV file'),
        cucm_file_browse_botton('Browse'),
        button('Next')
    ]
    return Sg.Window(window_title, layout, margins=(100, 100))


def w_file_not_found(current_window, cucm=False, folder=False):
    """File Not Found Window and Retry"""
    current_window.close()
    if cucm:
        layout = [
            gui_print('File or directory not found.'),
            gui_print('Select CUCM export CSV file'),
            cucm_file_browse_botton('Browse'),
            button('Retry')
        ]
    elif folder:
        layout = [
            gui_print('Directory not found.'),
            gui_print('Select folder to save Inventory Export'),
            folder_browse_botton('Browse'),
            button('Retry')
        ]
    else:
        layout = [
            gui_print('File or directory not found.'),
            gui_print('Select file containing device management IP addresses'),
            file_browse_botton('Browse'),
            button('Retry')
        ]
    return Sg.Window(window_title, layout, margins=(100, 100))


def w_invalid_file_entry(current_window, mgmt_file):
    """Invalid File Entry Window and Retry"""
    invalid_lines = 'Line    | Value\n'
    line_nums = mgmt_file.invalid_line_nums
    ip_addresses = mgmt_file.invalid_ip_addresses
    for (line_n, ip_addr) in zip(
            line_nums, ip_addresses):
        blank_space = ''
        for num1 in range(0, 10 - len(line_n)):
            blank_space += ' '
        invalid_lines += f'{line_n}{blank_space}  {ip_addr}'
    current_window.close()
    layout = [
        gui_print('Invalid File Entries'),
        gui_print_box(invalid_lines, size=(30, 15)),
        gui_print('Select file containing device management IP addresses'),
        file_browse_botton('Browse'),
        button('Retry')
    ]
    return Sg.Window(window_title, layout, margins=(100, 100))


def management_file_browse():
    """Window for selecting management file

    :return: Management file location"""
    current_window = w_mgmt_file_main()

    while True:
        event, values = current_window.read(timeout=10)
        if event == 'Check File' or event == 'Retry':
            try:
                Sg.user_settings_set_entry('-filename-', values['file'])
                file = MgmtIPAddresses(values['file'])
                if file.valid:
                    current_window.close()
                    return file.mgmt_ips
                else:
                    current_window = w_invalid_file_entry(current_window, file)
            except FileNotFoundError:
                current_window = w_file_not_found(current_window)
        if event == Sg.WIN_CLOSED:
            current_window.close()
            return None


def inventory_save_folder_browse():
    """Window for selecting inventory save location

    :return: Inventory file save folder location"""
    current_window = w_save_folder()

    while True:
        event, values = current_window.read(timeout=10)
        if event == 'Save File' or event == 'Retry':
            Sg.user_settings_set_entry('-folder-', values['folder'])
            if path.isdir(values['folder']):
                return values['folder']
            else:
                current_window = w_file_not_found(current_window, folder=True)
        if event == Sg.WIN_CLOSED:
            current_window.close()
            return None


class InventoryGui:
    """
    Front-end GUI for collecting inputs.

        Attributes:
            mgmt_ips - List of management IP addresses\n
            parsed_cucm_phones - Output from 'cucm_export_parse()'\n
            username - Network Username\n
            password - Network Password\n
            enable_pw - Enable Password
    """
    def __init__(self):
        current_window = w_mgmt_file_main()

        mgmt = False
        cucm = False

        while True:
            event, values = current_window.read(timeout=10)
            if (event == 'Next' or event == 'Retry') and not mgmt:
                try:
                    Sg.user_settings_set_entry('-filename-', values['file'])
                    file = MgmtIPAddresses(values['file'])
                    if file.valid:
                        self.mgmt_ips = file.mgmt_ips
                        """List of management IP addresses"""
                        mgmt = True
                        if values['cucm_export']:
                            current_window = w_cucm_file_main(current_window)
                            cucm = True
                        else:
                            current_window = w_credential(current_window)
                    else:
                        current_window = w_invalid_file_entry(current_window, file)
                except FileNotFoundError:
                    current_window = w_file_not_found(current_window)
            elif event == 'Next' and cucm:
                try:
                    Sg.user_settings_set_entry('-cucm_file-', values['cucm_file'])
                    self.parsed_cucm_phones = cucm_export_parse(values['cucm_file'])
                    """Output from 'cucm_export_parse()'"""
                    current_window = w_credential(current_window)
                except NoPhoneReportFound:
                    current_window = w_file_not_found(current_window, True)
            elif event == 'Run Inventory Discovery':
                self.username = values['user']
                """Network Username"""
                self.password = values['pass']
                """Network Password"""
                self.enable_pw = values['enable_pw']
                """Enable Password"""
                current_window.close()
                break
            if event == Sg.WIN_CLOSED:
                current_window.close()
                break

# def w_template(current_window, mgmt_file):
#     """Template Window"""
#     current_window.close()
#     layout = [
#         gui_print('Invalid File Entries'),
#         gui_print_box(invalid_lines, size=(30, 15)),
#         gui_print('Select file containing switch management IP addresses'),
#         file_browse_botton('Browse'),
#         button('Retry')
#     ]
#     return Sg.Window(window_title, layout, margins=(100, 100))
