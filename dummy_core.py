"""
This is the base code for the creation of dedicated cores for specific devices in the future. Take note 
that it is very likely that the core might look very different from what is suggested here due to very
different specifications from each device.

HOWEVER, YOU SHOULD BE ABLE TO FOLLOW THE SKELETON UP UNTIL

Creator = Ryan Lau Ler Young
Maintainer(s) = Walter Frank Pintor Ortiz, Lim Yu Ping, Ryan Lau Ler Young
Date = July 9th 2021
"""

import socket
import threading
import time
import re

import sys
import select

from opcua.client.client import Client

class modula:

    initialized = False
    set_dict = dict()
    get_dict = dict()
    plugin_ip = ''
    plugin_port=''
    format = 'ascii'

    def __init__(self, device_ip_arg = plugin_ip, device_port_arg = plugin_port ):
        """
        Constructor function
        """

        self.device_ip = device_ip_arg
        print ("[DEVICE_CORE] This is the device ip", self.device_ip)
        self.device_port = device_port_arg
        
        # Establish communication with computer that is hosting Modula Link
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setblocking(0)
        self.device_connect()

        # Constantly update the get_dict, but do not update the RESULT key value constantly
        self.get_dict = {
                        '''
                        'Machine': 1,
                        'Exit_Group': 1,
                        'Request_ID': 2000,
                        'STATUS': 0,
                        'POS1PICKTRAY': 0,
                        'POS2PICKTRAY': 0,
                        'POS1EXETRAY': 0,
                        'POS2EXETRAY': 0,
                        'RESULT': 0,
                        'ERROR': ''

                        ^^^ Here is an example of what the get_dict should have.

                        This dictionary is responsible for retrieving any information after a
                        query operation has been made, for example, getting the status of a robot

                        Add variables that the device would normally sent back to you after
                        a query operation or commanding operation was carried out.

                        For example, if the device returns the battery level (%), the corresponding
                        initialised key and value in this dictionary could be {'BATTERY_LEVEL': 0}

                        We have to specify the type of the value here as the plugin will detect the 
                        type(value in the dictionary) and create an OPC-UA variable on the server of
                        the same type.
                        '''
                        }

        self.set_dict = {
                        '''
                        'Machine': 0,
                        'Exit_Group': 0,
                        'Request_ID': 0,
                        'POSITION': 0,
                        'TRAY': 0,
                        'COMMAND': ''

                        ^^^ Here is an example of what the set_dict should have.

                        This dictionary is responsible for storing all the information required to send 
                        a valid command to the device to be executed, for example, moving a robot from 
                        point A to point B.

                        Add all the variables here that are required to make a whole command to be sent 
                        to the device for execution. [Take note that the {'COMMAND': ''} key-value pair 
                        needs to be here for the core to know which command that we would like to send to
                        the device]

                        So far, the TCP/IP communication protocols specified by the devices we have worked
                        with have a COMMAND string tagged to various kinds of tag-values.

                        For example, OMRON demands a bytes('goto GOAL1', 'utf-8), whereby the command is goto
                        and the tagged-value is GOAL1.

                        On your end, you have to examine the documents provided by the vendor, and find out
                        what specific variable that you need to have a full valid command.
                        '''
                        }


##################################################################################
#############################Threading Definitions################################
##################################################################################

    def start_thread(self):
        """
        This function spins a thread where the get dictionary is constantly updating
        """
        self.initialized = True
        print('[DEVICE_CORE] The service of start_thread has been initiated!\n')
        self.data_thread = threading.Thread(target=self.updating_get)
        self.data_thread.start()
        
    def stop_thread(self):
        """
        This function stops the thread where get dictionary is constantly updating
        """
        print('[DEVICE_CORE] The service of stop_thread has been executed!\n')
        self.initialized = False    

##################################################################################
###########################Communication Establisher##############################
##################################################################################

    def device_connect(self): 
        """
        This function attempts to establish a Websocket connection between the DEVICE_CORE and
        the Modula lift system.
        """
        connection_attempt = 1
        while connection_attempt < 30:
            try:
                self.s.connect((self.device_ip, self.device_port))
                time.sleep(1)
                break

            except KeyboardInterrupt:
                print('[DEVICE_CORE] Connection process was interrupted, shutting down...\n')
                self.s.close()

            except:
                print('[DEVICE_CORE] Failed connection.\nAttempt #' + str(connection_attempt) + ' to connect...\n')
                connection_attempt += 1
                time.sleep(0.5)

        print('[DEVICE_CORE] Connection has been established.') 

##################################################################################
########################Constant Update Get Dictonary#############################
##################################################################################
    
    def updating_get(self):
        """
        This function constantly updates the get dictionary for the modula_plugin to 
        read and write to the OPC server as a OPC client.
        """
        try: 
            while self.initialized:
                self.get_device_status()
                msg = ''
                
                try:
                    ready = select.select([self.s], [], [], 1)

                    if ready[0]:
                        msg = msg + self.s.recv(1024).decode(self.format)
                    
                    time.sleep(0.05)

                except Exception as e:
                    print("[DEVICE_CORE] STOP! Error when writing values from Modula Lift System,", e)

                print("[DEVICE_CORE] Here is the full unclean information received:", msg)
                
                # We need to clean the string with regular expression
                arr = self.get_regex_splitting(msg)

                # Pass arr to method to update the get_dict
                self.receive_and_update_get(arr)          

        except Exception as e:
            self.s.close()

##################################################################################
################################Get the STATUS####################################
##################################################################################  

    def get_device_status(self):
        '''
        machine_num = self.get_dict['Machine']
        exit_group = self.get_dict['Exit_Group']
        request_id = self.get_dict['Request_ID']
        command = 'STATUS'
        full_command = str(machine_num) + str(exit_group) + '|' + str(request_id) + '|' + command + '|' + '\n\r'
        self.s.send(bytes(full_command, self.format))
        
        ^^^ This is an example of how we got the status of the MODULA vertical lift system.

        As you can see here, 
        '''
        
##################################################################################
#########################Supporting get STATUS Functions##########################
##################################################################################
    '''
    You will notice that there exist two regex_splitting methods defined for both
    the get and set portions of the core. It was theorised (by Ryan), that if the 
    same function is called at the same time, there will be some sort of conflict.
    '''

    def get_regex_splitting(self, string):
        pattern = '\w+'
        string_split_array = re.findall(pattern, string)
        print('[DEVICE_CORE] The get result after regex splitting is:', string_split_array)
        return string_split_array
    
    def receive_and_update_get(self, arr):
        if (len(arr) > 1):
            prefix = arr[0]
            request_id = arr[1]
            # The value at index 2 is not required, because it is STATUS
            status = arr[3]
            pos1picktray = arr[4]
            pos2picktray = arr[5]
            pos1exetray = arr[6]
            pos2exetray = arr[7]

            self.get_dict['Machine'] = int(prefix[:-1])
            self.get_dict['Exit_Group'] = int(prefix[-1])
            self.get_dict['Request_ID'] = int(request_id)
            self.get_dict['STATUS'] = int(status)
            self.get_dict['POS1PICKTRAY'] = int(pos1picktray)
            self.get_dict['POS2PICKTRAY'] = int(pos2picktray)
            self.get_dict['POS1EXETRAY'] = int(pos1exetray)
            self.get_dict['POS2EXETRAY'] = int(pos2exetray)
        
        elif len(arr) == 1:
            self.get_dict['ERROR'] = arr[0]
            print('[DEVICE_CORE] Error encountered, ' + arr[0] + '.Please resolve the issue.\n')


##################################################################################
##############################Send Set Commands###################################
##################################################################################
    """
    This section defines all the send commands that Modula needs to run its operation. 
    The plugin will call the send_set_command. 
    """

    def send_set_command(self):
        command = self.set_dict['COMMAND']
        machine_num = self.set_dict['Machine']
        exit_group = self.set_dict['Exit_Group']
        request_id = self.set_dict['Request_ID']
        tray = self.set_dict['TRAY']
        position = self.set_dict['POSITION']
        
        if command == 'CALL':
            full_command = str(machine_num) + str(exit_group) + '|' + str(request_id) + '|' + command + '|' + str(tray) + '|' + str(position) + '\n\r'
            self.s.send(bytes(full_command, self.format))
            time.sleep(0.1)
            self.receive_and_update_set()

        elif command == 'RETURN':
            full_command = str(machine_num) + str(exit_group) + '|' + str(request_id) + '|' + command + '|' + str(position) + '\n\r'
            self.s.send(bytes(full_command, self.format))
            time.sleep(0.1)
            self.receive_and_update_set()
            
        else:
            print('[DEVICE_CORE] Send command is invalid, please try again.\n')
            self.get_dict['ERROR'] = 'BAD_COMMAND'


##################################################################################
#########################Supporting Set Command Functions#########################
##################################################################################
    '''
    You will notice that there exist two regex_splitting methods defined for both
    the get and set portions of the core. It was theorised (by Ryan), that if the 
    same function is called at the same time, there will be some sort of conflict.
    '''

    def receive_and_update_set(self):
        ready = select.select([self.s], [], [], 1)

        if ready[0]:
            time.sleep(0.5)
            msg = self.s.recv(1024).decode(self.format)
            print('[MODULE_CORE] Here is the information received after sending set command: ' + msg)
            # Call support function to carry out regex splitting on the received 
            # message and get back the array of strings
            arr = self.set_regex_splitting(msg)

            if len(arr) > 1:
                self.get_dict['RESULT'] = int(arr[3])
                self.get_dict['ERROR'] = 'NO ERROR'

            elif len(arr) == 1:
                self.get_dict['ERROR'] = arr[0]
                print('[DEVICE_CORE] Error encountered, ' + arr[0] + '.Please resolve the issue.\n')
    
    def set_regex_splitting(self, string):
        pattern = '\w+'
        string_split_array = re.findall(pattern, string)
        print('[DEVICE_CORE] The set result after regex splitting is:', string_split_array)

        return string_split_array

##################################################################################
###############################FOR DEBUGGING######################################
##################################################################################
    '''
    This is for testing the DEVICE_CORE
    '''
# # Testing the HostServer Core Class
# Mymodula = modula(device_ip_arg="192.168.170.33", device_port_arg=11000)

# modula.start_thread(Mymodula)
# time.sleep(10) 
# modula.stop_thread(Mymodula)
# After reaching the 10 seconds, the broken pipe error appears