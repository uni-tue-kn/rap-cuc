#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from TLV import TLV 
from Failure_code import Failure_code
from Vlan_context_tlv import Vlan_context_tlv


class Redundancy_control_tlv:
    def __init__(self, r_tag_status = False, vlan_context_list = []):
        self.__TYPE_ID = 0x24
        
        self.r_tag_status = r_tag_status # 1 bit usigned int with 7 bit succeeding padding L = 1
        if self.r_tag_status is False or True:
            pass
        else:
            raise ValueError('Invalid r tag status')


        self.vlan_context_stlv_list = vlan_context_list # L = variable

    def serialize(self):
        r_tag_status_formated = int(self.r_tag_status) << 7
        
        if self.vlan_context_stlv_list is []:
            raise ValueError('Invalid number of VLAN contexts') 

        length = 1
        value = bytearray([r_tag_status_formated])

        print(value)

        if self.vlan_context_stlv_list is []: 
            raise ValueError('List of Vlan contexts can not be empty!')
        else:
            for vlan_context in self.vlan_context_stlv_list:
                vlan_bytes = vlan_context.serialize()        
                length = length + len(vlan_bytes)
                value = value +  vlan_bytes
                print(value)

        tlv = TLV.encapsulate_object(self.__TYPE_ID, length, value)

        return tlv

    def deserialize(self, tlv):
        print(tlv)
        value, rest = TLV.extract(tlv)

        self.r_tag_status = int.from_bytes(value[0:1], byteorder='big', signed=False) >> 7
        if self.r_tag_status is 1 or 0:
            self.r_tag_status = bool(self.r_tag_status)
        else:
            raise ValueError('Invalid r tag status')
        
        self.vlan_context_stlv_list = []

        print(value)
        
        if len(value) > 1: 
            start = 1 
            print("value len: " + str(len(value)))

            print("start_oben:" + str(start))
            while start < len(value)-1:

                offset = value[start+1] * 256 + value[start+2] + 2
                print("start offset: " + str(offset))

                if value[start] == 0x25: # is vlan_context_stlv:
                    vlan = Vlan_context_tlv()
                    vlan.deserialize(value[start:start+offset+1])

                    self.vlan_context_stlv_list.append(vlan)

                    start = start + offset + 1
                print("start_unten:" + str(start))

    def dump(self):
        """ Dump object to console"""
        obj = self
        for attr in dir(obj):
            print("obj.%s = %r" % (attr, getattr(obj, attr)))

        for vlan_context in self.vlan_context_stlv_list:
            vlan_context.dump()






