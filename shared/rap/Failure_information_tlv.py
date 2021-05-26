#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import binascii

from .TLV import TLV
from .Failure_code import Failure_code

class Failure_information_tlv:
    def __init__(self, mac= '00-00-00-00-00-00', failure_code = Failure_code.ERROR):
        self.__TYPE_ID = 0x026
        self.__SYSTEM_ID_LEN = 8
        self.__FAILURE_CODE_LEN = 1
        
        if (len(mac) != 17):
            raise ValueError("Invalid MAC address")

        mac = mac.replace('-', '')
        mac = bytearray.fromhex(mac)
        self.system_id = bytearray(2) + mac  # L = 8 (prepending 2 bytes are 0 and then 6 bytes MAC)

        self.failure_code = failure_code  # L = 1

    def __btos(self, number):
        return binascii.hexlify(bytearray([number])).decode("utf-8")

    def get_system_id(self):
        s = self.system_id

        system_id_string = self.__btos(s[0]) + "-" + self.__btos(s[1]) + "-" + self.__btos(s[2]) + "-" \
                           + self.__btos(s[3]) + "-" + self.__btos(s[4]) + "-" + self.__btos(s[5]) + "-" \
                           + self.__btos(s[6]) + "-" + self.__btos(s[7])
        return system_id_string

    def serialize(self):
        """ This Method serializes the object to byte array containing the TLV structures """
        system_id_bytes = bytearray(self.system_id)
        failure_code_bytes = bytearray(self.failure_code.value.to_bytes(self.__FAILURE_CODE_LEN, byteorder = 'big'))

        tlv = TLV.encapsulate_object(self.__TYPE_ID, len(system_id_bytes + failure_code_bytes), system_id_bytes + failure_code_bytes)

        return tlv

    def deserialize(self, tlv):
        """ This Method builds an object from a byte array """
        value, rest = TLV.extract(tlv)

        self.system_id = value[0:8]
        self.failure_code = Failure_code(value[8])

        return len(value) + 3

    def dump(self):
        obj = self
        for attr in dir(obj):
            print("obj.%s = %r" % (attr, getattr(obj, attr)))



