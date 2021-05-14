#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from TLV import TLV

class Data_frame_parameters_tlv:
    def __init__(self, dst_mac_address = '00-00-00-00-00-00', vlan_id=0, priority=0):
        self.__TYPE_ID = 0x21

        self.dst_mac_address = bytearray.fromhex(dst_mac_address.replace('-',''))
        self.vlan_id = vlan_id # L = 12 bit
        self.priority = priority # L = 3 bit
        self.reserved = 0 # 1 bit reserved 
        
        if (self.vlan_id > 4095):
            raise ValueError("Invalid VLAN-ID")
        if (self.priority > 7):
            raise ValueError("Invalid VLAN-ID")

    def serialize(self):
        """ This Method serializes the object to string"""

        compound_field = ((self.vlan_id << 3) | self.priority) << 1

        value = self.dst_mac_address + compound_field.to_bytes(2, 'big')
        length = 8  

        return TLV.encapsulate_object(self.__TYPE_ID, length, value)

    def deserialize(self, tlv ):
        """ This Method builds an object from a string"""

        value, rest = TLV.extract(tlv)

        if (len(value) != 8):
            raise ValueError("Invalid data frame parameter tlv")

        self.dst_mac_address = value[0:6]

        compound_field = int.from_bytes(value[6:8], byteorder='big', signed=False) >> 1
        
        self.vlan_id = compound_field >> 3
        self.priority = compound_field & 0x07


    def dump(self):
        """ Dump object to console"""
        obj = self
        for attr in dir(obj):
            print("obj.%s = %r" % (attr, getattr(obj, attr)))


