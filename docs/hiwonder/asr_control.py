#!/usr/bin/python3
# coding=utf8
import smbus
import time

'''
/****************************************************
  Company:   Hiwonder
  Author:Shenzhen Hiwonder Technology Co., Ltd
  Shop:https://www.hiwonder.com/
*****************************************************
  Sensor: Hiwonder Series Integrated Voice Interaction Module
  Communication method：iic
  Return: Digital Value
*****************************************************/
'''


I2C_ADDR = 0x34  # I2C address

# Module Registers
ASR_RESULT_ADDR = 0x64  #Voice recognition result register address. Continuously reading this address helps determine if speech is recognized, with different values corresponding to different speech types.
ASR_SPEAK_ADDR = 0x6E   #Speech broadcast setting register address

ASR_CMDMAND = 0x00     #Speech type: Command word broadcast
ASR_ANNOUNCER = 0xFF   #Speech type: General announcement

class ASRModule:
    def __init__(self,address, bus=1):
        # Initialize I2C bus and device address
        self.bus = smbus.SMBus(bus)  # Use I2C bus 1
        self.address = address  # Device's I2C address
        self.send = [0, 0]  # Initialize the data array for sending

    def wire_write_byte(self, val):
        """
         Write a single byte to the device
        :param val: The byte value to be written
        :return: Returns True if the write is successful, False if it fails
        """
        try:
            self.bus.write_byte(self.address, val) # Send byte to the device
            return True # Write successful
        except IOError:
            return False # Write failed, return False

    def wire_write_data_array(self, reg, val, length):
        """
        Write a byte array to a specified register
        :param reg: The register address
        :param val: The byte array to be written
        :param length: The number of bytes to be written
        :return: Returns True if the write is successful, False if it fails
        """
        try:            
            self.bus.write_i2c_block_data(self.address, reg, val[:length]) # Send a byte array to the specified register of the device
            return True # Write successful
        except IOError:
            return False # Write failed, return False

    def wire_read_data_array(self, reg, length):
        """
        Read a byte array from a specified register
        Read a byte array from a specified register
        :param reg: The register address
        :param length: The number of bytes to be read
        :return: The byte array read, or an empty array if reading fails
        """          
        try:
            result = self.bus.read_i2c_block_data(self.address, reg, 1) # Read a byte array from the device
            return result # Return the read result
        except IOError:
            return [] # Read failed, return an empty array

    def rec_recognition(self):
        """
        Read recognition result
        :return: The recognition result, returns 0 if reading fails
        """
        result = self.wire_read_data_array(ASR_RESULT_ADDR, 1) # Read a byte from the result register
        if result:
            return result # Return the result read
        return 0  # Return 0 if no result is read

    def speak(self, cmd, id):
        """
        Send a speech command to the device
        :param cmd: The command byte
        :param id: The speech ID
        """
        if cmd == ASR_ANNOUNCER or cmd == ASR_CMDMAND: # Check if the command is valid
            self.send[0] = cmd # Set the first element of the send array to the command
            self.send[1] = id # Set the second element of the send array to the ID
            self.wire_write_data_array(ASR_SPEAK_ADDR, self.send, 2) # Send the command and ID to the specified register


if __name__ == "__main__":
    asr_module = ASRModule(I2C_ADDR)    
    # Define the broadcast content and its corresponding ID
    announcements = [
        (ASR_CMDMAND, 1),  # Moving forward
        (ASR_CMDMAND, 3),  # Turning left
        (ASR_ANNOUNCER, 1),  # Recyclable material
        (ASR_ANNOUNCER, 3)   # Hazardous waste
    ]
    
    while True:
        for cmd, id in announcements:
            asr_module.speak(cmd, id)
            time.sleep(5) 
        