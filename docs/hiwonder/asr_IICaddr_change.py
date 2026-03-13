#!/usr/bin/python3
# coding=utf8
import smbus
import time

'''
/****************************************************
  Company:  Hiwonder (公司：幻尔科技)
  Author: Shenzhen Hiwonder Technology Co., Ltd. (作者：深圳市幻尔科技有限公司)
  Online Shop: www.hiwonder.com (我们的店铺:lobot-zone.taobao.com)
*****************************************************
  Sensor: Hiwonder series integrated voice interaction module (传感器：Hiwonder系列 一体化语音交互模块)
  Communication method: IIC (通信方式：iic)
  Return: Digital (返回：数字量)
*****************************************************/
'''


I2C_ADDR = 0x34  # Default I2C address (默认I2C地址)

# Module Registers (模块寄存器)
ASR_RESULT_ADDR = 0x64  #Voice recognition result register address. By continuously reading this address's value, we determine whether speech is recognized. Different values correspond to different speech commands. (语音识别结果寄存器地址，通过不断读取此地址的值判断是否识别到语音，不同的值对应不同的语音)
ASR_SPEAK_ADDR = 0x6E   #Speech output setting register address (播报设置寄存器地址)
ASR_IIC_ADDR_CHANGE_ADDR = 0x03 #IIC device address register (IIC设备地址寄存器)

ASR_CMDMAND = 0x00     #Type: Command word speech (播报语类型：命令词条播报语)
ASR_ANNOUNCER = 0xFF   #Type: Regular speech (播报语类型：普通播报语)

class ASRModule:
    def __init__(self,address, bus=1):
        # Initialize I2C bus and device address (初始化 I2C 总线和设备地址)
        self.bus = smbus.SMBus(bus)  # Use I2C bus 1 (使用 I2C 总线 1)
        self.address = address  # Device I2C address (设备的 I2C 地址)
        self.send = [0, 0]  # Initialize the array for sending data (初始化发送数据的数组)

    def wire_write_byte(self, val):
        """
         Write a single byte to the device (向设备写入单个字节)
        :param val: The byte value to write (要写入的字节值)
        :return: Return True if successful, False if failed (如果成功写入返回 True，失败返回 False)
        """
        try:
            self.bus.write_byte(self.address, val) # Send byte to device (发送字节到设备)
            return True # Write successful (写入成功)
        except IOError:
            return False # Write failed (写入失败，返回 False)

    def wire_write_data_array(self, reg, val, length):
        """
        Write a byte array to a specified register (向指定寄存器写入字节数组)
        :param reg: Register address (寄存器地址)
        :param val: The byte array to write (要写入的字节数组)
        :param length: The number of bytes to write (要写入的字节数)
        :return: Return True if successful, False if failed (如果成功写入返回 True，失败返回 False)
        """
        try:            
            self.bus.write_i2c_block_data(self.address, reg, val[:length]) # Send byte array to specified register (发送字节数组到设备的指定寄存器)
            return True # Write successful (写入成功)
        except IOError:
            return False # Write failed, return False (写入失败，返回 False)

    def wire_read_data_array(self, reg, length):
        """
        Read a byte array from a specified register (从指定寄存器读取字节数组)
        :param reg: Register address (寄存器地址)
        :param length: The number of bytes to read (要读取的字节数)
        :return: The byte array read, returns an empty array if failed (读取到的字节数组，失败时返回空数组)
        """          
        try:
            result = self.bus.read_i2c_block_data(self.address, reg, 1) # Read byte array from device (从设备读取字节数组)
            return result # Return the result (返回读取结果)
        except IOError:
            return [] # Read failed (读取失败，返回空数组)

    def rec_recognition(self):
        """
        Read recognition result (识别结果读取)
        :return: Recognition result, returns 0 if reading fails (识别结果，如果读取失败返回 0)
        """
        result = self.wire_read_data_array(ASR_RESULT_ADDR, 1) # Read one byte from result register (从结果寄存器读取一个字节)
        if result:
            return result # Return the result (返回读取到的结果)
        return 0  # If no result, return 0 (如果没有结果，返回 0)

    def speak(self, cmd, id):
        """
        Send a speech command to the device (向设备发送说话命令)
        :param cmd: Command byte (命令字节)
        :param id: The speech ID (说话的 ID)
        """
        if cmd == ASR_ANNOUNCER or cmd == ASR_CMDMAND: # Check if the command is valid (检查命令是否有效)
            self.send[0] = cmd # Set the first element of the send array to the command (设置发送数组的第一个元素为命令)
            self.send[1] = id # Set the second element of the send array to the ID (设置发送数组的第二个元素为 ID)
            self.wire_write_data_array(ASR_SPEAK_ADDR, self.send, 2) # Send command and ID to the specified register (发送命令和 ID 到指定寄存器)

    def ChangeAddr(self, new_addr):
        """
        Send IIC address change command to the device (向设备发送IIC地址修改命令)
        :new_addr: New IIC address, optional values: 0x33, 0x34 (new_addr: 新IIC地址，可选值0x33、0x34)
        """
        if new_addr == 0x33 or new_addr == 0x34:
            self.wire_write_data_array(ASR_IIC_ADDR_CHANGE_ADDR, [new_addr],1)
            self.address = new_addr
            return 1
        else:
            return 0


if __name__ == "__main__":
    asr_module = ASRModule(I2C_ADDR)    
    # Define the broadcast content and its corresponding ID (定义播报内容及其对应的ID)
    announcements = [
        (ASR_CMDMAND, 1),  # Going straight (正在前进)
        (ASR_ANNOUNCER, 1),  # Recyclable waste (可回收物)
    ]
    
    while True:
        time.sleep(1)
		
        print("now,asr module's IIC Address is 0x34!")
        if(asr_module.ChangeAddr(0x34)):
            print("Success!")
            time.sleep(0.1)

            for cmd, id in announcements:
                asr_module.speak(cmd, id)
                time.sleep(2)	
				
        else:
            print("Fail!")


        time.sleep(1)
		
        print("now,asr module's IIC Address is 0x33!")
        if(asr_module.ChangeAddr(0x33)):
            print("Success!")
            time.sleep(0.1)
			
            for cmd, id in announcements:
                asr_module.speak(cmd, id)
                time.sleep(2) 
			
        else:
            print("Fail!")  
 
        