#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import binascii
from .TLV import TLV


# CID 00-80-CS is the uid of the descriptions defined by the 802.1Qdd standard in the appendix
# For the custom classes in this protoype shall be use EF-EF-EF as CID
class RACA:

    def __init__(self, raca_list=[]):
        self.__TYPE_ID = 0x00

        self.ra_class_desc_list = raca_list

    def serialize(self):

        value = bytearray()
        for ra_class_desc in self.ra_class_desc_list:
            value += ra_class_desc.serialize()

        return TLV.encapsulate_object(self.__TYPE_ID, len(value), value)

    def deserialize(self, tlv):

        value, rest = TLV.extract(tlv)

        rest = value
        while rest != bytearray(b''):

            value, rest = TLV.extract(rest)

            ra_class_desc = Ra_class_descriptor()
            ra_class_desc.deserialize(value)

            self.ra_class_desc_list.append(ra_class_desc)


class Ra_class_descriptor:
    def __init__(self, rsid='00-80-C2-01', priority=0x0):
        self.__TYPE_ID = 0x20
        self.priority = priority # L = 1

        rsid_clean = rsid.replace('-', '')
        self.rsid = bytearray.fromhex(rsid_clean)   # L = 4, 00-80-C2 as prefix
        self.organizationally_defined_stlv = None

    def __btos(self, number):
        return binascii.hexlify(bytearray([number])).decode("utf-8")

    def get_rsid(self):
        s = self.rsid
        rsid_id_string = self.__btos(s[0]) + "-" + self.__btos(s[1]) + "-" + self.__btos(s[2]) + "-" \
                           + self.__btos(s[3])
        return rsid_id_string

    def serialize(self):
        """ This Method serializes the object to string"""
        prio = bytearray([self.priority])

        value = prio + self.rsid

        return TLV.encapsulate_object(self.__TYPE_ID, len(value), value)

    def deserialize(self, tlv):
        """ This Method builds an object from a string"""

        #value, rest = TLV.extract(tlv)
        value = tlv

        self.priority = value[0]
        self.rsid = value[1:5]







