#!/usr/bin/env python3
# -*- coding: utf-8 -*-


class TLV:
    # Type = 1
    # Len  = 2
    # Val  = Variable 

    def __init__(self):
        pass 

    @staticmethod
    def encapsulate_object(type, length, value):
        """ Encapsulate value(byte array with length as length) object with type (8bit) and length (16bit) and return as byte array """
        
        length_h = int(length / 256)
        length_l = length % 256 

        # @TODO add sanity checks
        s = bytearray([type, length_h, length_l]) + value
        return s

    @staticmethod
    def extract(tlv):
        """ Return the value of the given TLV as a byte string"""
        length = tlv[1] * 256 + tlv[2]
        
        # @TODO add sanity checks

        return tlv[3:length + 3], tlv[length + 3 :]



