#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import binascii
from .TLV import TLV
from .Data_frame_parameters_tlv import Data_frame_parameters_tlv
from .Msrp_tspec_tlv import Msrp_tspec_tlv
from .Token_bucket_tspec_tlv import Token_bucket_tspec_tlv
from .Redundancy_control_tlv import Redundancy_control_tlv
from .Vlan_context_tlv import Vlan_context_tlv
from .Failure_information_tlv import Failure_information_tlv
from .Failure_code import Failure_code
from .Interface_configuration_tlv import Interface_configuration_tlv


class TAA:
    def __init__(self, stream_id="00-00-00-00-00-00:00-00", stream_rank=0, destination_mac='00-00-00-00-00-00',
                 vlan_id=0x0, priority=0x0, msrp_tspec=None, token_bucket_tspec=None, organizationally_defined=None):
        self.__TYPE_ID = 0x01

        stream_id_clean = stream_id.replace(':', '')
        stream_id_clean = stream_id_clean.replace('-', '')
        stream_id_clean = bytearray.fromhex(stream_id_clean)

        self.stream_id = stream_id_clean  # L = 8
        if (len(self.stream_id) != 8):
            raise ValueError("Invalid Stream-ID")

        self.stream_rank = stream_rank # L = 1
        self.accumulated_maximum_latency = 0 # L = 4
        self.data_frame_parameters_stlv = Data_frame_parameters_tlv(destination_mac, vlan_id, priority) # L = 11
        self.token_bucket_tspec_stlv = token_bucket_tspec # L = 19 , L = 0 if msrp > 0
        self.msrp_tspec_stlv = msrp_tspec # L = 7, L = 0 if token bucket > 0
        self.redundancy_control_stlv = None # L = variable, only used for multi-context TAAs
        self.failure_information_stlv = None # L = variable
        self.interface_configuration = None  # L = variable
        self.organizationally_defined_stlv = organizationally_defined

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

    def get_dst_mac(self):
        s = self.data_frame_parameters_stlv.dst_mac_address
        mac = str(s[0]) + "-" + str(s[1]) + "-" + str(s[2]) + "-" + str(s[3]) + "-" + str(s[4]) + "-" \
                           + str(s[5])
        return mac

    def get_mac(self):
        s = self.stream_id
        mac = self.__btos(s[0]) + "-" + self.__btos(s[1]) + "-" + self.__btos(s[2]) + "-" \
                           + self.__btos(s[3]) + "-" + self.__btos(s[4]) + "-"  + self.__btos(s[5])
        return mac

    def serialize(self):
        """ This Method serializes the object to string"""
        tspec = None
        
        value = self.stream_id + self.stream_rank.to_bytes(1, 'big') + \
                self.accumulated_maximum_latency.to_bytes(4, 'big')

        data_frame_spec = self.data_frame_parameters_stlv.serialize()
        value = value + data_frame_spec

        if self.msrp_tspec_stlv is not None:
            tspec = self.msrp_tspec_stlv.serialize()
            value = value + tspec
        elif self.token_bucket_tspec_stlv is not None:
            tspec = self.token_bucket_tspec_stlv.serialize()
            value = value + tspec

        if self.redundancy_control_stlv is not None:
            tspec = self.redundancy_control_stlv.serialize()
            value = value + tspec

        if self.failure_information_stlv is not None:
            tspec = self.failure_information_stlv.serialize()
            value = value + tspec

        if self.interface_configuration is not None:
            inter_conf = self.interface_configuration.serialize()
            value = value + inter_conf

        if self.organizationally_defined_stlv is not None:
            org_tlv = self.organizationally_defined_stlv.serialize()
            value = value + org_tlv

        length = len(value)

        return TLV.encapsulate_object(self.__TYPE_ID, length, value)

        

    def deserialize(self, tlv):
        """ This Method builds an object from a string"""

        value, rest = TLV.extract(tlv)
        self.stream_id = value[0:8]
        self.stream_rank = value[8]
        self.accumulated_maximum_latency = int.from_bytes(value[9:13], 'big')
        self.data_frame_parameters_stlv = Data_frame_parameters_tlv()
        self.data_frame_parameters_stlv.deserialize(value[13:24])

        next_index = 24
        if value[24] == 0x22: # token bucket tspec
            self.token_bucket_tspec_stlv = Token_bucket_tspec_tlv()
            next_index = 43
            self.token_bucket_tspec_stlv.deserialize(value[24:next_index], next_index)
        elif value[24] == 0x23: # MSRP tspec
            self.msrp_tspec_stlv = Msrp_tspec_tlv()
            next_index = 31
            self.msrp_tspec_stlv.deserialize(value[24:next_index])

        if len(value) > next_index and value[next_index] == 0x24: # Redundancy Control
            offset = value[next_index + 1] * 256 + value[next_index + 2] + 3
            self.redundancy_control_stlv = Redundancy_control_tlv()
            self.redundancy_control_stlv.deserialize(value[next_index:next_index + offset])
            next_index += offset

        if len(value) > next_index and value[next_index] == 0x26: # Failure information
            offset = value[next_index + 1] * 256 + value[next_index + 2] + 3
            self.failure_information_stlv = Failure_information_tlv()
            self.failure_information_stlv.deserialize(value[next_index:next_index + offset])
            next_index += offset

        if len(value) > next_index and value[next_index] == 0xFF: # Interface Config
            offset = value[next_index + 1] * 256 + value[next_index + 2] + 3
            self.interface_configuration = Interface_configuration_tlv()
            self.interface_configuration.deserialize(value[next_index:next_index + offset])
            next_index += offset

        if len(value) > next_index and value[next_index] == 0x27: # Time aware spec org tlv
            offset = value[next_index + 1] * 256 + value[next_index + 2] + 3
            self.organizationally_defined_stlv = Org_defined_taa_tlv()
            self.organizationally_defined_stlv.deserialize(value[next_index:next_index + offset])
            next_index += offset

    def add_failure_information(self, mac, failure_code):
        """ Add a failure information sub-TLV to TAA

            mac             is the mac address for the stream_id
            failure_code    is the failure code from 802.1Qcc (Table 46-15)
        """
        self.failure_information_stlv = Failure_information_tlv(mac, failure_code)

    def remove_failure_information(self):
        """ Add a failure information sub-TLV to TAA

            mac             is the mac address for the stream_id
            failure_code    is the failure code from 802.1Qcc (Table 46-15)
        """
        self.failure_information_stlv = None

    def add_redundancy_control(self, r_tag_status, vlan_context_list):
        """ Add a redundancy control sub-TLV to TAA for multi-context announcements
        """

        self.redundancy_control_stlv = Redundancy_control_tlv(r_tag_status, vlan_context_list)

    def add_interface_configuration(self, json_string):
        inter_conf = Interface_configuration_tlv()
        inter_conf.parse_from_json(json_string)
        self.interface_configuration = inter_conf

    def add_org_defined(self, org_tlv):
        self.organizationally_defined_stlv = org_tlv

    def increase_accumulated_latency(self, summand):
        self.accumulated_maximum_latency += summand

    def dump(self):
        """ Dump object to console"""
        obj = self
        for attr in dir(obj):
            print("obj.%s = %r" % (attr, getattr(obj, attr)), flush=True)

        if self.failure_information_stlv is not None:
            self.failure_information_stlv.dump()

        if self.redundancy_control_stlv is not None:
            self.redundancy_control_stlv.dump()

        if self.msrp_tspec_stlv is not None:
            self.msrp_tspec_stlv.dump()

        if self.token_bucket_tspec_stlv is not None:
            self.token_bucket_tspec_stlv.dump()

        if self.data_frame_parameters_stlv is not None:
            self.data_frame_parameters_stlv.dump()

        if self.organizationally_defined_stlv is not None:
            self.organizationally_defined_stlv.dump()

    def dump_pretty(self):
        stream = "---------------------------------------------------------------- \n" \
                 "Talker Announce Attribute \nStream_id: %s \nAccumulated Latency: %s\n" \
                 % (self.get_stream_id(), self.accumulated_maximum_latency)

        fail = ""
        if self.failure_information_stlv is not None:
            fail = "Failure_code: %s\n" % self.failure_information_stlv.failure_code
            fail += "Failure_system_id: %s\n" % self.failure_information_stlv.get_system_id()

        ic = ""
        if self.interface_configuration is not None:
            ic = "Interface configuration: \n destination mac: %s \n source mac: %s \n pcp: %s \n vlan_id: %s  \
                  \n \
                ----------------------------------------------------------------" % (
                self.interface_configuration.get_dst_mac(),
                  self.interface_configuration.get_src_mac(),
                  self.interface_configuration.vlan_tag_tlv.priority_code_point,
                  self.interface_configuration.vlan_tag_tlv.vlan_id)

        log_msg = stream + fail + ic
        print(log_msg, flush=True)

        return log_msg


class Org_defined_taa_tlv:
    def __init__(self, interval_numerator=0, interval_denominator=0, earliest_transmit_offset=0, latest_transit_offset=0, jitter=0, maximum_latency=0):
        self.__TYPE_ID = 0x27
        self.ocid = bytearray.fromhex("EFEFEF")

        self.interval_numerator = interval_numerator  # L = 4
        self.interval_denominator = interval_denominator  # L = 4
        self.earliest_transmit_offset = earliest_transmit_offset  # L = 4
        self.latest_transmit_offset = latest_transit_offset  # L = 4
        self.jitter = jitter  # L = 4
        self.maximum_latency= maximum_latency  # L = 4

    def serialize(self):

        value = self.ocid + self.interval_numerator.to_bytes(4, "big") + self.interval_denominator.to_bytes(4, "big") \
                + self.earliest_transmit_offset.to_bytes(4, "big") + self.latest_transmit_offset.to_bytes(4, "big") \
                + self.jitter.to_bytes(4, "big") \
                + self.maximum_latency.to_bytes(4, "big")

        return TLV.encapsulate_object(self.__TYPE_ID, len(value), value)

    def deserialize(self, tlv):
        value, rest = TLV.extract(tlv)

        self.interval_numerator = int.from_bytes(value[3:7], byteorder='big', signed=False)
        self.interval_denominator = int.from_bytes(value[7:11], byteorder='big', signed=False)
        self.earliest_transmit_offset = int.from_bytes(value[11:15], byteorder='big', signed=False)
        self.latest_transmit_offset = int.from_bytes(value[15:19], byteorder='big', signed=False)
        self.jitter = int.from_bytes(value[19:23], byteorder='big', signed=False)
        self.maximum_latency = int.from_bytes(value[23:27], byteorder='big', signed=False)

    def dump(self):
        obj = self
        for attr in dir(obj):
            print("obj.%s = %r" % (attr, getattr(obj, attr)))


