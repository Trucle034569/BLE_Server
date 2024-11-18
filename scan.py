#!/usr/bin/python3

import asyncio
import logging
from bleak import BleakClient, BleakScanner
import sys

WEIGHT_MEASUREMENT_UUID = "00002A9D-0000-1000-8000-00805F9B34FB"
SCALE_NAME = "MI SCALE2"

logger = logging.getLogger('my_logger')
logger.setLevel(logging.DEBUG)

# send logs to the terminal
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('[%(levelname)s] %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


class GlobalState:

    def __init__ (self):
        self.__weight = 0
        self.__callback = None
    
    def add_callback(self, callback):
        self.__callback = callback
        
    def update_weight(self, value):
        self.__weight = value
        if self.__callback:
            self.__callback(self.__weight)
        
global_state = GlobalState()

# add timeout and message when not found to this function
async def scan_scale():
    logger.info(f"Finding {SCALE_NAME}...")
    return await BleakScanner.find_device_by_name(SCALE_NAME, timeout=30.0)
        
    
def handle_notification(sender, data: bytearray):
    weight = int.from_bytes(data[1:3], byteorder='little') / 200
    print (f"receive: {weight} kg")
    global_state.update_weight(weight)
    

async def get_weight_data():
    scale = await scan_scale()
    if scale is None:
        logger.error("Connection timeout")
        return
    
    async with BleakClient(scale.address) as client:
        try:
            connected = client.is_connected
            if not connected:
                logger.info(f"Connecting to {SCALE_NAME}")
                connected = await client.connect()

            if connected :
                logger.info(f"Connected to {SCALE_NAME} successfully")
                await client.start_notify(WEIGHT_MEASUREMENT_UUID, handle_notification)
                
                await asyncio.sleep(30)
                
                await client.stop_notify(WEIGHT_MEASUREMENT_UUID)
            else:
                logger.error(f"Failed to connect to {SCALE_NAME}")
        except Exception as e:
            print("An error occurred: %s", e)
            
        finally:
            await client.disconnect()

asyncio.run(get_weight_data())