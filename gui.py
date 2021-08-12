import PySimpleGUI as Sg
from net_async import MgmtIPAddresses

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


def button(string, font=m_font):
    return [Sg.Button(str(string), font=font, bind_return_key=True)]


def dropdown(input_list, font=m_font):
    return [Sg.Combo(input_list, font=font, bind_return_key=True)]


def file_browse_botton(string, font=m_font):
    return [
        Sg.Input(Sg.user_settings_get_entry('-filename-', ''), key='file'),
        Sg.FileBrowse(str(string), initial_folder='./', font=font)]


def w_main(current_window=None):
    """Main / Home Window"""
    if current_window is not None:
        current_window.close()
    layout = [
        gui_print('Select file containing device management IP addresses'),
        file_browse_botton('Browse'),
        button('Check File')
    ]
    return Sg.Window(window_title, layout, margins=(100, 100))


def w_file_not_found(current_window):
    """File Not Found Window and Retry"""
    current_window.close()
    layout = [
        gui_print('File or directory not found.'),
        gui_print('Select file containing switch management IP addresses'),
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


class ManagementFileBrowseWindow:
    def __init__(self):
        current_window = w_main()
        self.mgmt_ips = None

        while True:
            event, values = current_window.read(timeout=10)
            if event == 'Check File' or event == 'Retry':
                try:
                    Sg.user_settings_set_entry('-filename-', values['file'])
                    file = MgmtIPAddresses(values['file'])
                    if file.valid:
                        self.mgmt_ips = file.mgmt_ips
                        break
                    else:
                        current_window = w_invalid_file_entry(current_window, file)
                except FileNotFoundError:
                    current_window = w_file_not_found(current_window)
            if event == 'Main Page':
                current_window = w_main(current_window)
            if event == Sg.WIN_CLOSED:
                break
        current_window.close()

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
