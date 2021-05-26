#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .TLV import TLV

class Token_bucket_tspec_tlv:
    def __init__(self, max_trans_frame_size = 0, min_trans_frame_size = 0, commited_information_rate = 0, commited_burst_size = 0):
        self.__TYPE_ID = 0x22

        self.max_trans_frame_size = max_trans_frame_size # L = 2
        self.min_trans_frame_size = min_trans_frame_size # L = 2
        self.commited_information_rate = commited_information_rate #L = 8 
        self.commited_burst_size = commited_burst_size # L = 4

        if (self.max_trans_frame_size > 0xFFFF):
            raise ValueError("Invalid max_trans_frame_size")

        if (self.min_trans_frame_size > 0xFFFF):
            raise ValueError("Invalid max_trans_frame_size")

        if (self.commited_information_rate > 0xFFFFFFFFFFFFFFFF): # 8 byte 
            raise ValueError("Invalid max_trans_frame_size")
        
        if (self.commited_burst_size > 0xFFFFFFFF):
            raise ValueError("Invalid max_trans_frame_size")

    def serialize(self):
        """ This method serializes the object to string"""
         
        value = self.max_trans_frame_size.to_bytes(2, "big") + self.min_trans_frame_size.to_bytes(2, "big") + self.commited_information_rate.to_bytes(8,"big") + self.commited_burst_size.to_bytes(4, "big")
        
        lenght = len(value)

        return TLV.encapsulate_object(self.__TYPE_ID, lenght, value)

    def deserialize(self, tlv):
        """ This method builds an object from a string"""

        value, rest = TLV.extract(tlv)

        if (len(value) != 16):
            raise ValueError("Invalid tocken bucket tlv")

        self.max_trans_frame_size       = int.from_bytes(value[0:2], byteorder='big', signed=False)
        self.min_trans_frame_size       = int.from_bytes(value[2:4], byteorder='big', signed=False)
        self.commited_information_rate  = int.from_bytes(value[4:12], byteorder='big', signed=False)
        self.commited_burst_size        = int.from_bytes(value[12:16], byteorder='big', signed=False)

    def dump(self):
        """ Dump object to console"""
        obj = self
        for attr in dir(obj):
            print("obj.%s = %r" % (attr, getattr(obj, attr)))



