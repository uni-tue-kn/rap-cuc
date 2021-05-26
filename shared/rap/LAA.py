#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import binascii
import sys

sys.path.insert(0, '/app/shared/rap/')

from .Listener_status import Listener_status
from .TLV import TLV
from .Failure_information_tlv import Failure_information_tlv
from .Interface_configuration_tlv import Interface_configuration_tlv
from .Failure_code import Failure_code  # For test code at bottom

class LAA:
    def __init__(self, stream_id= "00-00-00-00-00-00:00-00"):
        self.__TYPE_ID = 0x02

        stream_id_clean = stream_id.replace(':', '')
        stream_id_clean = stream_id_clean.replace('-', '')
        stream_id_clean = bytearray.fromhex(stream_id_clean)

        self.stream_id = stream_id_clean  # L = 8
        if (len(self.stream_id) != 8):
            raise ValueError("Invalid Stream-ID")

        
        self.listener_attach_status = Listener_status.NONE # L = 1
        self.failure_information_stlv = None # L = 0 | 9
        self.interface_configuration = None  # this is not standard conform (possible feature for the future)
        self.organizationally_defined_stlv = [] # L = variable

    def get_type(self):
        return self.__TYPE_ID

    def __btos(self, number):
        return binascii.hexlify(bytearray([number])).decode("utf-8")

    def get_stream_id(self):
        s = self.stream_id
        stream_id_string = self.__btos(s[0]) + "-" + self.__btos(s[1]) + "-" + self.__btos(s[2]) + "-" \
                           + self.__btos(s[3]) + "-" + self.__btos(s[4]) + "-"  + self.__btos(s[5]) + ":" \
                           + self.__btos(s[6]) + "-" + self.__btos(s[7])
        return stream_id_string

    def serialize(self):
        """ This Method serializes the object to byte array containing the TLV structures """
        stream_id_bytes = bytearray(self.stream_id)
        listener_status_bytes = bytearray([self.listener_attach_status.value])
    
        length = len(stream_id_bytes + listener_status_bytes )
        value = stream_id_bytes + listener_status_bytes 

        if self.failure_information_stlv is not None: 
            failure_bytes = self.failure_information_stlv.serialize()        
            length = length + len(failure_bytes)
            value = value +  failure_bytes

        if self.interface_configuration is not None:
            inter_conf = self.interface_configuration.serialize()
            length = length + len(inter_conf)
            value = value + inter_conf

        tlv = TLV.encapsulate_object(self.__TYPE_ID, length, value)

        return tlv

    def deserialize(self, tlv):
        """ This Method builds an object from a string"""
        
        value, rest = TLV.extract(tlv)

        self.stream_id = value[0:8]
        self.listener_attach_status = Listener_status(value[8])
       
        if len(value) > 9: # optional sub-tlv is present
            if value[9] == 0x026: # is Failure_information_tlv
                fail_obj = Failure_information_tlv()
                fail_length = fail_obj.deserialize(value[9:])
                self.failure_information_stlv = fail_obj

                if len(value) > (9+fail_length):
                    inter_conf = Interface_configuration_tlv()
                    inter_conf.deserialize(value[9+fail_length:])
                    self.interface_configuration = inter_conf

            elif value[9] == 0x0FF:  # is interface configuration
                inter_conf = Interface_configuration_tlv()
                inter_conf.deserialize(value[9:])
                self.interface_configuration = inter_conf


            elif value[9] == 0x27: # is orga tlv
                self.organizationally_defined_stlv, rest = TLV.extract(rest) 

            else:
                raise ValueError("Invalid Sub TLV in LAA")

    def add_failure_information(self, mac, failure_code):
        """ Add a failure information sub-TLV to LAA

            mac             is the mac address for the stream_id 
            failure_code    is the failure code from 802.1Qcc (Table 46-15)
        """
        self.failure_information_stlv = Failure_information_tlv(mac, failure_code)

    def add_interface_configuration(self, json_string):
        inter_conf = Interface_configuration_tlv()
        inter_conf.parse_from_json(json_string)
        self.interface_configuration = inter_conf

    def remove_failure_information(self):
        """ Remove the failure information tlv"""
        self.failure_information_stlv = None

    def update_status(self, status):
        """ Update the status of the LAA, done by bridges or CUC"""
        self.listener_attach_status = status

    def dump(self):
        """ Dump object to console"""
        obj = self
        for attr in dir(obj):
            print("obj.%s = %r" % (attr, getattr(obj, attr)), flush=True)

        if self.failure_information_stlv is not None:
            self.failure_information_stlv.dump()
        return True

    def dump_pretty(self):
        stream = "---------------------------------------------------------------- \n" \
                 "Listener Attach Attribute \nStream_id: %s \nStatus: %s\n" \
                 % (self.get_stream_id(), self.listener_attach_status)

        fail = ""
        if self.failure_information_stlv is not None:
            fail = "Failure_code: %s\n" % self.failure_information_stlv.failure_code
            fail += "Failure_system_id: %s\n" % self.failure_information_stlv.get_system_id()

        ic = ""
        if self.interface_configuration is not None:
            ic = "Interface configuration: \n destination mac: %s \n source mac: %s \n pcp: %s \n vlan_id: %s  \
                  \n time aware offset: %s \n \
                ----------------------------------------------------------------"  % (
                self.interface_configuration.get_dst_mac(),
                  self.interface_configuration.get_src_mac(),
                  self.interface_configuration.vlan_tag_tlv.priority_code_point,
                  self.interface_configuration.vlan_tag_tlv.vlan_id,
                  self.interface_configuration.time_aware_offset)
        log_msg = stream + fail + ic
        print(log_msg, flush=True)
        return log_msg



