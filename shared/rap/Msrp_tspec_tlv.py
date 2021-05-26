#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .TLV import TLV

class Msrp_tspec_tlv:
    def __init__(self, max_frame_size = 0, max_interval_frames = 0):
        self.__TYPE_ID = 0x23

        self.max_frame_size = max_frame_size # L = 2
        self.max_interval_frames = max_interval_frames # L = 2

        if (self.max_frame_size > 0xFFFF):
            raise ValueError("Invalid maximum frame size")
        
        if (self.max_interval_frames > 0xFFFF):
            raise ValueError("Invalid interval frame maximum")


    def serialize(self):
        """ This method serializes the object to string"""

        length = 4
        value = self.max_frame_size.to_bytes(2, "big") + self.max_interval_frames.to_bytes(2, "big")
        
        tlv = TLV.encapsulate_object(self.__TYPE_ID, length, value)

        return tlv

    def deserialize(self, tlv):
        """ This method builds an object from a string"""
        
        value, rest = TLV.extract(tlv)

        if (len(value) != 4):
            raise ValueError("Invalid Stream-ID")

        self.max_frame_size = int.from_bytes(value[0:2], byteorder='big', signed=False)
        self.max_interval_frames = int.from_bytes(value[2:4], byteorder='big', signed=False)

    def dump(self):
        """ Dump object to console"""
        obj = self
        for attr in dir(obj):
            print("obj.%s = %r" % (attr, getattr(obj, attr)))




