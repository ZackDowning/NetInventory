# NetInventory
One-file executable for collecting information on Cisco Network Infrastructure devices.  

Inventory discovery will collect CDP neighbor information and append to Excel Workbook seperating devices  
by Routers_Switches, Phones, APs, Others, and Failed within seperate worksheets.
### Requirements
- Windows Operating System to run executable on
- Text file with list of management IP addresses for devices
  - Example: example.txt
    ```
    1.1.1.1
    2.2.2.2
    3.3.3.3
    ```
- Administration credentials for devices
- Devices running Cisco IOS, IOS-XE, or NX-OS operating system
- SSH or TELNET connectivity to devices to parse
- CUCM Export CSV File (Optional, See Below)
## GUI
### File Selection
![alt text](https://i.imgur.com/i8Wnz07.png)
- 'Use CUCM Export' option allows option to provide CUCM phone report associating phone discription and  
directory number to discovered phones.
#### CUCM Report Generation Instructions
1. Bulk Administration > Phone > Generate Phone Reports
2. Filter phones as desired
3. Device Fields: 'Description', 'Device Name'
4. Line Fields: 'Director Number'
5. (Recommended) Check: 'Run Immediately'
6. Check Job at Bulk Administration > Job Scheduler
7. Once complete, download file from Bulk Administration > Upload/Download Files
8. Change file extension from export to '.txt' to '.csv'
### If 'Use CUCM Export' Selected
![alt text](https://i.imgur.com/KWo5eKu.png)
### Management Credential Input
![alt text](https://i.imgur.com/wP9HDF7.png)
### Discovery
![alt text](https://i.imgur.com/4pNebwZ.png)

![alt text](https://i.imgur.com/2Qt24yT.png)
### File Save Location Selection
![alt text](https://i.imgur.com/PnOiDDq.png)
## Output Report
![alt text](https://i.imgur.com/g6UepTI.png)
![alt text](https://i.imgur.com/vFmWWEI.png)
![alt text](https://i.imgur.com/3xp1roC.png)
![alt text](https://i.imgur.com/321FBGX.png)
![alt text](https://i.imgur.com/euGOkle.png)