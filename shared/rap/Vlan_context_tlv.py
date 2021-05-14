#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from TLV import TLV 
from Failure_code import Failure_code
from Failure_information_tlv import Failure_information_tlv


class Vlan_context_tlv:
    def __init__(self, vlan_id= 0x000):
        self.__TYPE_ID = 0x25
        
        self.vlan_id = vlan_id   # 12 bit usigned int with 4 bit succeeding padding L = 2 
        if self.vlan_id > 0xFFF:
            raise ValueError('Invalid Vlan_id')

        self.failure_information_stlv = None  # L = 0 | 9

    def serialize(self):
        vlan_id_formated = self.vlan_id << 4 
        vlan_id_bytes = bytearray(2)
        vlan_id_bytes[0] = int(vlan_id_formated / 256)
        vlan_id_bytes[1] = vlan_id_formated % 256

        length = len(vlan_id_bytes)
        value = vlan_id_bytes 

        if self.failure_information_stlv is not None: 
            failure_bytes = self.failure_information_stlv.serialize()        
            length = length + len(failure_bytes)
            value = value +  failure_bytes

        tlv = TLV.encapsulate_object(self.__TYPE_ID, length, value)

        return tlv

    def deserialize(self, tlv):
        value, rest = TLV.extract(tlv)

        self.vlan_id = int.from_bytes(value[0:2], byteorder='big', signed=False) >> 4 

        if len(value) > 2: # optional sub-tlv is present
            if value[2] == 0x26: # is Failure_information_tlv
                fail_obj = Failure_information_tlv()
                fail_obj.deserialize(value[2:])
                self.failure_information_stlv = fail_obj

    def add_failure_information(self, mac, failure_code):
        """ Add a failure information sub-TLV

            mac             is the mac address for the stream_id 
            failure_code    is the failure code from 802.1Qcc (Table 46-15)
        """
        self.failure_information_stlv = Failure_information_tlv(mac, failure_code)

    def remove_failure_information(self):
        """ Remove the failure information tlv"""
        self.failure_information_stlv = None


    def dump(self):
        """ Dump object to console"""
        obj = self
        for attr in dir(obj):
            print("obj.%s = %r" % (attr, getattr(obj, attr)))

        if self.failure_information_stlv is not None:
            self.failure_information_stlv.dump()



