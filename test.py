import asyncio
import logging
from bleak import BleakClient, BleakScanner
import sys
import dbus


logger = logging.getLogger('my_logger')
logger.setLevel(logging.DEBUG)

# send logs to the terminal
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('[%(levelname)s] %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

class BLEWeightService:
    WEIGHT_MEASUREMENT_UUID = "00002A9D-0000-1000-8000-00805F9B34FB"
    SCALE_NAME = "MI SCALE2"
    
    def __init__ (self):
        self.__weight = 0
        self.__callback = None
    
    def add_callback(self, callback):
        self.__callback = callback  
        
    def get_weight(self):
        return self.__weight
        
    def get_weight_in_bytes(self):
        value = []
        
        strtemp = str(self.__weight) 
        for c in strtemp:
            value.append(dbus.Byte(c.encode()))

        return value

    async def scan_scale(self):
        logger.info(f"Finding {self.SCALE_NAME}...")
        return await BleakScanner.find_device_by_name(self.SCALE_NAME, timeout=30.0)
    
    def handle_notification(self, sender, data: bytearray):
        weight = int.from_bytes(data[1:3], byteorder='little') / 200
        self.__weight = weight
        if self.__callback:
            self.__callback(self.__weight)
        print (f"receive: {weight} kg")
    
    async def get_weight_data(self):
        scale = await self.scan_scale()
        if scale is None:
            logger.error("Connection timeout")
            return
        
        async with BleakClient(scale.address) as client:
            try:
                connected = client.is_connected
                if not connected:
                    logger.info(f"Connecting to {self.SCALE_NAME}")
                    connected = await client.connect()

                if client.is_connected :
                    logger.info(f"Connected to {self.SCALE_NAME} successfully")
                    await client.start_notify(self.WEIGHT_MEASUREMENT_UUID, self.handle_notification)
                    
                    await asyncio.sleep(30)
                    
                    await client.stop_notify(self.WEIGHT_MEASUREMENT_UUID)
                else:
                    logger.error(f"Failed to connect to {self.SCALE_NAME}")
            except Exception as e:
                logger.error("An error occurred: %s", e)
                
    def run_scanner(self):
        asyncio.run(self.get_weight_data())
        
        
my_scanner = BLEWeightService()
# my_scanner.run_scanner()
