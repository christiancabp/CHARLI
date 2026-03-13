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
  Sensor：Hiwonder Series All-in-One Voice Interaction Module
  Communication：iic
  Return：digital quantity
*****************************************************/
'''

# I2C address
I2C_ADDR = 0x34  # I2C address
ASR_RESULT_ADDR = 100  # ASR Voice Recognition Result Register Address (0x64)
ASR_SPEAK_ADDR = 110  # ASR Speech Broadcast Setting Register Address (0x6E)
ASR_CMDMAND = 0x00    # Speech Type: Command Word
ASR_ANNOUNCER = 0xFF  # Speech Type: General Announcement

class ASRModule:
    def __init__(self,address, bus=1):
        # Initialize the I2C bus and device address
        self.bus = smbus.SMBus(bus)  # Use I2C bus 1
        self.address = address  # I2C address of the device
        self.send = [0, 0]  # Initialize the list for sending data

    def wire_write_byte(self, val):
        """
        Write a single byte to the device
        :param val: The byte value to be written
        :return: Returns True if the write is successful, False otherwise
        """
        try:
            self.bus.write_byte(self.address, val) # Send byte to the device
            return True # Write successful
        except IOError:
            return False # Write failed, return False

    def wire_write_data_array(self, reg, val, length):
        """
        Write a list of bytes to a specified register
        :param reg: The register address
        :param val: The list of bytes to be written
        :param length: The number of bytes to be written
        :return: Returns True if the write is successful, False otherwise
        """
        try:            
            self.bus.write_i2c_block_data(self.address, reg, val[:length]) # Send byte list to the device's specified register
            return True # Write successful
        except IOError:
            return False # Write failed, return False

    def wire_read_data_array(self, reg, length):
        """
        Read a list of bytes from a specified register
        :param reg: The register address
        :param length: The number of bytes to be read
        :return: The list of bytes read, or an empty list if reading failed
        """          
        try:
            result = self.bus.read_i2c_block_data(self.address, reg, length) # Read byte list from the device
            return result # Return the read result
        except IOError:
            return [] # Read failed, return an empty list

    def rec_recognition(self):
        """
        Read recognition result
        :return: The recognition result, returns 0 if reading fails
        """
        result = self.wire_read_data_array(ASR_RESULT_ADDR, 1) # Read a byte from the result register
        if result:
            return result # Return the read result
        return 0  # Return 0 if no result is read

    def speak(self, cmd, id):
        """
        Send a speech command to the device
        :param cmd: The command byte
        :param id: 说话的 ID
        """
        if cmd == ASR_ANNOUNCER or cmd == ASR_CMDMAND: # Check if the command is valid
            self.send[0] = cmd # Set the first element of the send list to the command
            self.send[1] = id # Set the second element of the send list to the ID
            self.wire_write_data_array(ASR_SPEAK_ADDR, self.send, 2) # Send the command and ID to the specified register


if __name__ == "__main__":
    asr_module = ASRModule(I2C_ADDR)    
    while True:
        recognition_result = asr_module.rec_recognition()
        if recognition_result[0] != 0:
            if recognition_result[0] == 1:
                print("go")
            elif recognition_result[0] == 2:
                print("back")
            elif recognition_result[0] == 3:
                print("left")
            elif recognition_result[0] == 4:
                print("right")
            elif recognition_result[0] == 9:
                print("stop")