#!/usr/bin/python3


import dbus
import scan
import json
from advertisement import Advertisement
from service import Application, Service, Characteristic, Descriptor
from test import my_scanner


GATT_CHRC_IFACE = "org.bluez.GattCharacteristic1"

NOTIFY_TIMEOUT = 5000



class WeightScaleAdvertisement(Advertisement):
    def __init__(self, index):
        Advertisement.__init__(self, index, "peripheral")
        self.add_local_name("Weight Scale")
        self.include_tx_power = True
        
class ThermometerService(Service):
    WEIGHT_SVC_UUID = "00000001-cbd6-4d25-8851-18cb67b7c2d9"

    def __init__(self, index):

        Service.__init__(self, index, self.WEIGHT_SVC_UUID, True)
        self.add_characteristic(WeightCharacteristic(self))
        
class WeightCharacteristic(Characteristic):
    WEIGHT_CHARACTERISTIC_UUID = "00000002-cbd6-4d25-8851-18cb67b7c2d9"
    
    def __init__(self, service):
            self.notifying = False
            my_scanner.add_callback(self.set_weight_callback)
            Characteristic.__init__(
                    self, self.WEIGHT_CHARACTERISTIC_UUID,
                    ["notify", "read"], service)
            self.add_descriptor(WeightDescriptor(self))
    
    # def data_parser(self, value):
    #     value = []
        
    #     strtemp = str(value) 
    #     for c in strtemp:
    #         value.append(dbus.Byte(c.encode()))

    #     return value

    def set_weight_callback(self, data):
        if self.notifying:
            self.PropertiesChanged(GATT_CHRC_IFACE, {"Value": data}, [])

        return self.notifying

    def StartNotify(self):
        if self.notifying:
            return

        self.notifying = True

        value = my_scanner.get_weight_in_bytes()
        self.PropertiesChanged(GATT_CHRC_IFACE, {"Value": value}, [])

    def StopNotify(self):
        self.notifying = False

    def ReadValue(self, options):
        value = my_scanner.get_weight_in_bytes()

        return value

class WeightDescriptor(Descriptor):
    WEIGHT_DESCRIPTOR_UUID = "2901"
    WEIGHT_DESCRIPTOR_VALUE = "Fake data"

    def __init__(self, characteristic):
        Descriptor.__init__(
                self, self.WEIGHT_DESCRIPTOR_UUID,
                ["read"],
                characteristic)

    def ReadValue(self, options):
        value = []
        desc = self.WEIGHT_DESCRIPTOR_VALUE

        for c in desc:
            value.append(dbus.Byte(c.encode()))

        return value

my_scanner.run_scanner()

app = Application()
app.add_service(ThermometerService(0))
app.register()


adv = WeightScaleAdvertisement(0)
adv.register()

try:
    app.run()
except KeyboardInterrupt:
    app.quit()
