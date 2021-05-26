import json
import binascii

from .TLV import TLV



class Interface_configuration_tlv:
    ''' This class models the data for one item of the iterface_list in the interface configuration '''

    def __init__(self):
        self.__TYPE_ID = 0x0FF

        self.mac_addresses_tlv = None  # L = 12
        self.vlan_tag_tlv = None   # L = 2
        # self.ipv4_tuple_tlv = None   # Is not used by cnc thus omitted
        # self.ipv4_tuple_tlv = None   # Is not used by cnc thus omitted
        self.time_aware_offset = 0  # L = 4

    def serialize(self):
        """ This Method serializes the object to byte array containing the TLV structures """
        mac_tlv = self.mac_addresses_tlv.serialize()
        vlan_tlv = self.vlan_tag_tlv.serialize()
        tao = self.time_aware_offset.to_bytes(4, "big")

        value = mac_tlv + vlan_tlv + tao

        tlv = TLV.encapsulate_object(self.__TYPE_ID, len(value), value)

        return tlv

    def __btos(self, number):
        return binascii.hexlify(bytearray([number])).decode("utf-8")

    def get_dst_mac(self):
        s = self.mac_addresses_tlv.dst_mac
        mac = self.__btos(s[0]) + "-" + self.__btos(s[1]) + "-" + self.__btos(s[2]) + "-" + self.__btos(s[3]) + "-" + self.__btos(s[4]) + "-" \
              + self.__btos(s[5])
        return mac

    def get_src_mac(self):
        s = self.mac_addresses_tlv.src_mac
        mac = self.__btos(s[0]) + "-" + self.__btos(s[1]) + "-" + self.__btos(s[2]) + "-" + self.__btos(s[3]) + "-" + self.__btos(s[4]) + "-" \
              + self.__btos(s[5])
        return mac

    def deserialize(self, tlv):
        """ This Method builds an object from a byte array """
        value, rest = TLV.extract(tlv)

        mac_tlv = Mac_address_tlv()
        mac_tlv.deserialize(value[0:15])
        self.mac_addresses_tlv = mac_tlv

        vlan_tlv = Vlan_tag_tlv()
        vlan_tlv.deserialize(value[15:20])
        self.vlan_tag_tlv = vlan_tlv

        self.time_aware_offset = int.from_bytes(value[20:], byteorder="big", signed=False)

    def parse_from_json(self, json_string):

        interface_config = json.loads(json_string)
        dst_mac = interface_config['config-list'][0]['ieee802-mac-addresses']['destination-mac-address']
        src_mac = interface_config['config-list'][0]['ieee802-mac-addresses']['source-mac-address']

        pcp = interface_config['config-list'][1]['ieee802-vlan-tag']['priority-code-point']
        vlan_id = interface_config['config-list'][1]['ieee802-vlan-tag']['vlan-id']

        self.mac_addresses_tlv = Mac_address_tlv(src_mac=src_mac, dst_mac=dst_mac)  # L = 12
        self.vlan_tag_tlv = Vlan_tag_tlv(pcp=int(pcp), vlanid=int(vlan_id))   # L = 2
        # self.ipv4_tuple_tlv = None   # Is not used by cnc thus omitted
        # self.ipv4_tuple_tlv = None   # Is not used by cnc thus omitted
        if len(interface_config['config-list']) > 2:
            self.time_aware_offset = interface_config['config-list'][2]['time-aware-offset']

    def dump(self):
        obj = self
        for attr in dir(obj):
            print("obj.%s = %r" % (attr, getattr(obj, attr)))


class Mac_address_tlv:
    def __init__(self, src_mac='00-00-00-00-00-00', dst_mac='00-00-00-00-00-00'):

        self.__TYPE_ID = 0x0FE

        mac = dst_mac.replace('-', '')
        self.dst_mac = bytearray.fromhex(mac)

        mac = src_mac.replace('-', '')
        self.src_mac = bytearray.fromhex(mac)

    def serialize(self):
        value = self.dst_mac + self.src_mac
        return TLV.encapsulate_object(self.__TYPE_ID, len(value), value)

    def deserialize(self, tlv):
        value, rest = TLV.extract(tlv)
        self.dst_mac = value[0:6]
        self.src_mac = value[6:]


class Vlan_tag_tlv:
    def __init__(self, pcp=0x0, vlanid=0x000):
        self.__TYPE_ID = 0x0FD
        self.priority_code_point = pcp  # L = 3 bit
        self.reserved = 0               # L = 1 bit
        self.vlan_id = vlanid           # L = 12 bit

    def serialize(self):

        if self.vlan_id > 4095:
            raise ValueError("Vlan ID to large")

        value = (self.priority_code_point << 13) | self.vlan_id

        return TLV.encapsulate_object(self.__TYPE_ID, 2, value.to_bytes(2, "big"))

    def deserialize(self, tlv):
        value, rest = TLV.extract(tlv)

        value = int.from_bytes(value[:], byteorder='big', signed=False)

        self.vlan_id = value & 0xfff
        self.priority_code_point = value >> 13


