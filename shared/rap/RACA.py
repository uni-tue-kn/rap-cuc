#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import binascii
from TLV import TLV


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

    def add_org_defined(self, org_tlv):
        for raca_index in range(len(self.ra_class_desc_list)):
            self.ra_class_desc_list[raca_index].add_org_defined(org_tlv)

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

        if self.organizationally_defined_stlv is not None:
            value = value + self.organizationally_defined_stlv.serialize()

        return TLV.encapsulate_object(self.__TYPE_ID, len(value), value)

    def deserialize(self, tlv):
        """ This Method builds an object from a string"""

        #value, rest = TLV.extract(tlv)
        value = tlv

        self.priority = value[0]
        self.rsid = value[1:5]

        if len(value) > 5:
            if value[5] != self.__TYPE_ID:
                org = Org_defined_raca_tlv()
                org.deserialize(value[5:])
                self.add_org_defined(org)

    def add_org_defined(self, org_tlv):
        self.organizationally_defined_stlv = org_tlv


class Org_defined_raca_tlv:
    def __init__(self, interval_numerator=0, interval_denominator=0, earliest_transmit_offset=0, latest_transit_offset=0, jitter=0):
        self.__TYPE_ID = 0x27
        self.ocid = bytearray.fromhex("EFEFEF")

        self.interval_numerator = interval_numerator  # L = 4
        self.interval_denominator = interval_denominator  # L = 4
        self.earliest_transmit_offset = earliest_transmit_offset  # L = 4
        self.latest_transmit_offset = latest_transit_offset  # L = 4
        self.jitter = jitter  # L = 4

    def serialize(self):

        value = self.ocid + self.interval_numerator.to_bytes(4, "big") + self.interval_denominator.to_bytes(4, "big") \
                + self.earliest_transmit_offset.to_bytes(4, "big") + self.latest_transmit_offset.to_bytes(4, "big") \
                + self.jitter.to_bytes(4, "big")

        return TLV.encapsulate_object(self.__TYPE_ID, len(value), value)

    def deserialize(self, tlv):
        value, rest = TLV.extract(tlv)

        self.interval_numerator = int.from_bytes(value[3:7], byteorder='big', signed=False)
        self.interval_denominator = int.from_bytes(value[7:11], byteorder='big', signed=False)
        self.earliest_transmit_offset = int.from_bytes(value[11:15], byteorder='big', signed=False)
        self.latest_transmit_offset = int.from_bytes(value[15:19], byteorder='big', signed=False)
        self.jitter = int.from_bytes(value[19:23], byteorder='big', signed=False)


