#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-

import sys
from collections import OrderedDict
from dataclasses import dataclass

sys.path.insert(0, '..')
from shared.aux.logger import Logger
from shared.aux.msgQueue import MsgQueue
from shared.aux.msgQueuePacket import MsgQueuePacket
from shared.aux.msgType import MsgType

# Logger
loggerWrapper = Logger(__file__ + ".log")
logger = loggerWrapper.get_logger()

@dataclass
class RapParticipant:

    declarationList: dict  # "attributeId" : attributeTlv
    registrationList: dict  # "attributeId" : attributeTlv
    serMappingInfo: dict  # "recordNo" : [attributeIds]
    desMappingInfo: dict  # ""

    def declare_attribute(self, attribute_tlv):
        pass

    def withdraw_attribute(self, attribute_tlv):
        pass

    def register_attribute(self, attribute_tlv):
        pass

    def deregister_attribute(self, attribute_tlv):
        pass

    def generate_attribute_id(self, attribute_tlv):
        pass

#class AttributeDeclarationDatabase:

    def declare_attribute(self, inAttribute):
        pass

    def withdraw_attribute(self, inAttribute):
        pass

#class AttributeRegistrationDatabase:

    def register_attribute(self, inAttribute, inAttributeId):
        pass

    def deregister_attribute(self, inAttributeId):
        pass
    
    def reset_registration_database(self):
        pass

#class AttributeSerializationDatabase:

    def allocate_record_numbers(self):
        # Generate as uuIDs, standard allows to serialize multiple attributes in one records but we dismiss this idea
        pass

    def updateSerMappingInfo(self, inAttributeId):
        """
        @param inAttributeId:
        @return: outRecordNumber and outAttributeIdList
        """
        pass
    def serializeAttribute(self, inAttributeId):
        """ Issues a LRP_WRITE_RECORD_REQ to trigger transport of the attribute via LRP
        @param inAttributeId:
        @return:
        """
        pass

#AttributeDeserializationDatabase:

    def deserialize_attribute(self, inRecord):
        """
        Invoked after receiving a LRP_RECORD_WRITTEN_IND

        @return:
        """
        pass
    
    def reset_portal_registrar_database(self):
        """ Issues a LRP_DELETE_RECORD_REQ for each recordNo in the desMappingInfo
        @return:
        """
        pass

@dataclass
class RapParticipantSM:
    """
    The Rap Participant controls declaration/withdrawal of attributes
    and reacts to record written events of the LRP task. It notifies RAP CUC about registered
    and deregistered attributes
    """

    def __init__(self, queue_register: dict):
        self.queue_register = queue_register

        # State machine of the corresponding task
        # Includes a mapping from msgTypes to handler function to serve requests/indications from other tasks
        self.states = {
            # todo add states
            MsgType.LRP_FIRST_HELLO_IND: self.process_first_hello,
            MsgType.LRP_PORTAL_STATUS_IND: self.process_portal_status,
            MsgType.LRP_RECORD_WRITTEN_IND: self.process_record_written,
            MsgType.RPSI_DECLARE_REQ: self.declare_attribute,
            MsgType.RPSI_WITHDRAW_REQ: self.withdraw_attribute,
        }

    def process_first_hello(self, q_pckt: MsgQueuePacket) -> None:
        """ Process the first hello indication for portal creation
        Answer with a associate portal request
        @param q_pckt:
        """
        pass

    def process_portal_status(self, q_pckt: MsgQueuePacket) -> None:
        """ Process a portal status indication for portal creation
        @param q_pckt: portalId, associationStatus
        """
        pass

    def process_record_written(self, q_pckt: MsgQueuePacket) -> None:
        """ LRP task indicates that a new record was received. Process the record, store it as an attribute in RDB,
        and message the RAP-CUC
        @param q_pckt: portalId, recordNo, data
        """
        pass


    def declare_attribute(self, q_pckt: MsgQueuePacket) -> None:
        """ Declare an attribute on behalf of the RAP-CUC. Arranges transmission with LRP task.
        @param q_pckt:
        """
        pass


    def withdraw_attribute(self, q_pckt: MsgQueuePacket) -> None:
        """ Withdraw an attribute on behalf of the RAP-CUC. Arranges transmission with LRP task.
        @param q_pckt:
        """
    pass
