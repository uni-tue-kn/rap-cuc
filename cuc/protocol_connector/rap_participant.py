#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-
import copy
import os
import sys
import json
from collections import OrderedDict
from dataclasses import dataclass, field

sys.path.insert(0, '..')
from shared.aux.logger import Logger
from shared.aux.msgQueue import MsgQueue
from shared.aux.pollableQueue import PollableQueue
from shared.aux.msgQueuePacket import MsgQueuePacket
from shared.aux.msgType import MsgType
from shared.rap.TAA import TAA
from shared.rap.LAA import LAA
from shared.rap.RACA import RACA

# Logger
loggerWrapper = Logger(__file__ + ".log")
logger = loggerWrapper.get_logger()

@dataclass
class RapParticipant:
    participantId: int
    localTargetPortInfo: dict  # Read in from file since Portal Discovery Mode is static
    lrp_queue: PollableQueue
    protocol_connector_queue: MsgQueue
    #staticNeighborTargetPortInfo  # Not reaquired since CUC does not use Neighbour Target Port Requests

    portalId: int = -1  # Portal Id received from the First Hello Indication, default -1 to show that it is not set
    partEnabled: bool = True # Indicates if participant is enabled
    portalCreated: bool = False  # Indicates if portal is established

    declarationList: OrderedDict = field(default_factory=OrderedDict)  # "attributeId" : attributeTlv
    serMappingInfo: OrderedDict = field(default_factory=OrderedDict)  # "recordNo" : [attributeIds]

    registrationList: OrderedDict = field(default_factory=OrderedDict) # "attributeId" : attributeTlv
    desMappingInfo: OrderedDict = field(default_factory=OrderedDict)  # "recordNo" : [attributeIds]

    #localTargetPortOper
    neighborDiscoveryMode: int = 2  # 1 = lldp; 2 = static; 3 = Exploratory Hello
    helloTime: int = 30  #
    completeListTimerReset = -1  # used for local target port req, not yet specified by Qdd
    exploreHelloRecvEnabled: bool = False  # No Exploratory Hello LRPDUs accepted

    # LLDP Discovery
    #lldpNeighborTargetPortInfo
    #lastNeighborTargetPortInfo
    #lldpNeighborInfoNew
    #lldpNeighborInfoMismatch

    portalInitiated: bool = False
    portalConnected: bool = False
    associationApproved: bool = False
    neighborRegistrarOverflow = False  # indicates an overflow condition in the neighbour's portal

    appId: str = "00-80-C2-01"
    attributeIdToRecordNoMapping: OrderedDict = field(default_factory=OrderedDict)   # attributeId : record number
    recordNoCounter: int = 0  # the current highest record number

# RAP Service Interface
    def declare_attribute(self, attribute_tlv):
        self.declare_attribute_db(attribute_tlv)

    def withdraw_attribute(self, attribute_tlv):
        self.withdraw_attribute_db(attribute_tlv)

    def register_attribute(self, attribute_tlv):  # attributeId is passed only for that function according to 802.1Qdd?
        self.register_attribute_db(attribute_tlv, self.generate_attribute_id(attribute_tlv))

    def deregister_attribute(self, attribute_tlv):
        self.deregister_attribute_db(attribute_tlv)

    @classmethod
    def generate_attribute_id(self, attribute_tlv):
        """ Generate an attribute ID for the three main attribute types of RAP (RACA, TAA, LAA)
        @param attribute_tlv:
        @return: The attribute ID as a string
        """
        type = attribute_tlv.get_type()

        if type == 0x00:
            attribute: RACA = attribute_tlv

            return "raca"

        elif type == 0x01:
            attribute: TAA = attribute_tlv

            return attribute.get_stream_id() + "-" + str(attribute.data_frame_parameters_stlv.vlan_id)

        elif type == 0x02:
            attribute: LAA = attribute_tlv
            return attribute.get_stream_id()

    #class Portal Maintenance
    #def checkLldpNeighbourInfo(self):

    # not required in this implemenation
    def destroyPortal(self):
        pass

    # not required in this implementation
    def resetDatabases(self):
        pass

    def initiatePortalCreation(self):

        msg = {
            "participantId" : self.participantId,  # not defined by standard, used to map socket of lrp to participant
            "appId" : self.appId,
            "localTargetPortInfo" : self.localTargetPortInfo,
            "helloTime" : self.helloTime,
            "applicationInformation" : 0x00,
            "cplCompleteListTimerReset" : self.completeListTimerReset
        }

        self.lrp_queue.send_msg(msg=MsgQueuePacket(MsgType.LRP_LOCAL_TARGET_PORT_REQ, msg), sender_name="rap_participant")

        # todo for real LRP implementation: check if portal really was initiated (lrp needs to respond to request)
        self.portalInitiated = True

    def processFirstHello(self, firstHelloIndication: dict):
        """ Process the Hello LRPDU(hsLooking) from LRP to create a portal with a neighbour.
            Answer with an Associate Portal Request
        @param firstHelloIndication:
        @return:
        """

        self.portalId = firstHelloIndication["portalId"]
        self.portalCreated = True

        helloLrpdu = firstHelloIndication["helloLrpdu"]
        # todo for real LRP implementation: check if hello LRPDU contains the right application information
        association_allowed = True

        msg = {
            "portalId" : self.portalId,
            "allowed": association_allowed,
        }
        self.lrp_queue.send_msg(msg=MsgQueuePacket(MsgType.LRP_ASSOCIATE_PORTAL_REQ, msg), sender_name="rap_participant")

    def processPortalStatusInd(self, portalStatusInd):
        """ Process the portal status indication which indicates receit of receipt of a Hello LRPDU(hsConnected).
            Data transmission and receipt is ready after here.
        @param portalStatusInd:
        @return:
        """

        if self.portalCreated == False:
            logger.error("Portal not connected!")
            return
        if portalStatusInd["portalId"] != self.portalId:
            logger.error("Portal IDs do not match!")
            return

        if portalStatusInd["associationStatus"] == "connected":
            self.portalConnected = True
            self.neighborRegistrarOverflow = portalStatusInd["NeighborRegistrarDatabaseOverflow"]
        elif portalStatusInd["associationStatus"] == "disconnected":
            self.portalConnected = False
            self.handlePortalDisconnection()

    def handlePortalDisconnection(self):
        """ Disconnect Portal if the Hello LRPDU indicates erroneous connection establishment.
        @return:
        """
        self.reset_registration_database()
        self.reset_portal_registrar_database()
        self.desMappingInfo.clear()
        pass

#class AttributeDeclarationDatabase:

    def declare_attribute_db(self, inAttribute):
        attribute_id = self.generate_attribute_id(inAttribute)
        self.declarationList[attribute_id] = inAttribute
        self.serializeAttribute(attribute_id)

    def withdraw_attribute_db(self, inAttribute):
        attribute_id = self.generate_attribute_id(inAttribute)
        if attribute_id not in self.declarationList:
            return

        self.declarationList.pop(attribute_id)
        self.serializeAttribute(attribute_id)

#class AttributeRegistrationDatabase:

    def register_attribute_db(self, inAttribute, inAttributeId):

        self.registrationList[inAttributeId] = inAttribute

        # Indicate attribute registration to rap cuc
        msg = {
            "participantId": self.participantId,
            "attribute": inAttribute
        }
        self.protocol_connector_queue.send_msg(msg=MsgQueuePacket(MsgType.RPSI_REGISTER_IND, msg), sender_name="rap_participant")

    def deregister_attribute_db(self, inAttributeId):
        if inAttributeId not in self.registrationList:
            return

        attribute = self.registrationList.pop(inAttributeId)

        # Indicate attribute registration to rap cuc
        msg = {
            "participantId": self.participantId,
            "attribute": attribute
        }
        self.protocol_connector_queue.send_msg(msg=MsgQueuePacket(MsgType.RPSI_DEREGISTER_IND, msg),
                                               sender_name="rap_participant")

    def reset_registration_database(self):

        # if registration list is empty
        if not bool(self.registrationList):
            return

        for attribute_id in list(self.registrationList.keys()):
            self.deregister_attribute_db(inAttributeId=attribute_id)

#class AttributeSerializationDatabase:

    def allocate_record_numbers(self, attributeId):
        # Generate as uuIDs, standard allows to serialize multiple attributes in one records but include only one

        if not self.attributeIdToRecordNoMapping.get(attributeId):
            self.attributeIdToRecordNoMapping[attributeId] = self.recordNoCounter
            self.recordNoCounter += 1

        return self.attributeIdToRecordNoMapping[attributeId]

    def updateSerMappingInfo(self, inAttributeId):
        """
        @param inAttributeId:
        @return: outRecordNumber and outAttributeIdList
        """
        attributeToDeclare = self.declarationList.get(inAttributeId)
        isInMappingInfo = False
        recordNo = -1

        for recNo, attributeIdList in self.serMappingInfo.items():
            if inAttributeId in attributeIdList:
                isInMappingInfo = True
                recordNo = recNo
                break

        # New Declaration
        if (attributeToDeclare is not None) and isInMappingInfo is False:
            recordNo = self.allocate_record_numbers(inAttributeId)
            self.serMappingInfo[recordNo] = [inAttributeId]
        # withdrawal of declared attribute
        elif (attributeToDeclare is None) and isInMappingInfo is True:
            self.serMappingInfo[recordNo].remove(inAttributeId)

        attributeIdList = self.serMappingInfo[recordNo]

        if attributeIdList is []:
            self.serMappingInfo.pop(recordNo)

        return recordNo, attributeIdList

    def serializeAttribute(self, inAttributeId):
        """ Issues a LRP_WRITE_RECORD_REQ to trigger transport of the attribute via LRP
        @param inAttributeId:
        @return:
        """
        recordNo, attributeIdList = self.updateSerMappingInfo(inAttributeId=inAttributeId)
        serializedData = bytearray(0)

        if attributeIdList is not []:
            if len(attributeIdList) == 1:
                attribute = self.declarationList[attributeIdList[0]]
                serializedData = attribute.serialize()
            else:
                pass
                # The standard support multiple attributes in one record.
                # We simplify implementation by assuming a single attribute per record.

        msg = {
            "portalId": self.portalId,
            "recordNo": recordNo,
            "data": serializedData
        }
        self.lrp_queue.send_msg(msg=MsgQueuePacket(MsgType.LRP_WRITE_RECORD_REQ, msg),
                                               sender_name="rap_participant")

    #AttributeDeserializationDatabase:

    def deserialize_attribute(self, inRecordWrittenInd):
        """ Invoked after receiving a LRP_RECORD_WRITTEN_IND
        @param inRecordWrittenInd: contains a dict with portalId, recordNo, data
        @return:
        """
        portalId = inRecordWrittenInd["portalId"]
        recordNo = inRecordWrittenInd["recordNo"]
        data = inRecordWrittenInd["data"]
        attributeList = []
        attributeIds = []
        mapping = {}

        if portalId != self.portalId:
            return

        if len(data) > 0:
            attribute = None
            if data[0] == 0x00:  #RACA
                attribute = RACA()
                attribute.deserialize(data)
                attributeList.append(attribute)
            elif data[0] == 0x01:  #TAA
                attribute = TAA()
                attribute.deserialize(data)
                attributeList.append(attribute)
            elif data[0] == 0x02:  #LAA
                attribute = LAA()
                attribute.deserialize(data)
                attributeList.append(attribute)

            for attribute in attributeList:
                attributeId = self.generate_attribute_id(attribute)
                attributeIds.append(attributeId)
                mapping[attributeId] = attribute

        # new record
        if not self.desMappingInfo.get(recordNo):
            self.desMappingInfo[recordNo] = attributeIds
            for attribute in attributeList:
                self.register_attribute_db(attribute, self.generate_attribute_id(attribute))
        # record already registered
        else:
            localList = self.desMappingInfo[recordNo]
            residual = copy.deepcopy(localList)
            for attributeId in attributeIds:
                # new attribute
                if attributeId not in localList:
                    self.register_attribute_db(mapping[attributeId], attributeId)
                    self.desMappingInfo[recordNo].append(attributeId)
                    residual.remove(attributeId)
                # update attribute
                elif attributeId in localList:
                    self.register_attribute_db(mapping[attributeId], attributeId)
                    residual.remove(attributeId)
            # deregister attributes known locally, but not present in latest received record
            for attributeId in residual:
                self.deregister_attribute_db(attributeId)
                self.desMappingInfo[recordNo].remove(attributeId)

            # Delete Mapping entry when all records are deregistered
            if self.desMappingInfo[recordNo] == []:
                self.desMappingInfo.pop(recordNo)

        return

    def reset_portal_registrar_database(self):
        """ Issues a LRP_DELETE_RECORD_REQ for each recordNo in the desMappingInfo
        @return:
        """
        if self.desMappingInfo == {}:
            return
        for recordNo in self.desMappingInfo.keys():
            msg = {
                "portalId" : self.portalId,
                "recordNo" : recordNo
            }
            self.lrp_queue.send_msg(msg=MsgQueuePacket(MsgType.LRP_DELETE_RECORD_REQ, msg),
                                                   sender_name="rap_participant")
        self.serMappingInfo = OrderedDict()


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
            MsgType.RPSI_DECLARE_REQ: self.declare_attribute_request,
            MsgType.RPSI_WITHDRAW_REQ: self.withdraw_attribute_request,
        }
        self.rapParticipants = []

        localTargetPortInfo = open(
            os.path.dirname(os.path.realpath('__file__')) + "/protocol_connector/localTargetPortInfo.json").read()
        localTargetPortInfo = json.loads(localTargetPortInfo)

        # Instantiate RAP Participants
        for targetPortInfo in localTargetPortInfo["localTargetPorts"]:
            self.rapParticipants.append(RapParticipant(participantId=(len(self.rapParticipants)),
                                                       localTargetPortInfo=targetPortInfo,
                                                       lrp_queue=self.queue_register["lrp_dummy"],
                                                       protocol_connector_queue=self.queue_register["protocol_connector"]))

        # Instantiate RAP Participants
        for rapParticipant in self.rapParticipants:
            rapParticipant.initiatePortalCreation()

    def get_partipipant_by_id(self, participantId):

        for rapp in self.rapParticipants:
            if rapp.participantId == participantId:
                return rapp
        return None

    def get_partipipant_by_portalid(self, portalid):
        for rapp in self.rapParticipants:
            if rapp.portalId == portalid:
                return rapp
        return None

    def process_first_hello(self, q_pckt: MsgQueuePacket) -> None:
        """ Process the first hello indication for portal creation
        Answer with a associate portal request
        @param q_pckt:
        """
        rapp = self.get_partipipant_by_id(q_pckt.message["participantId"])
        rapp.processFirstHello(q_pckt.message)

    def process_portal_status(self, q_pckt: MsgQueuePacket) -> None:
        """ Process a portal status indication for portal creation
        @param q_pckt: portalId, associationStatus
        """
        rapp = self.get_partipipant_by_portalid(q_pckt.message["portalId"])
        rapp.processPortalStatusInd(q_pckt.message)

    def process_record_written(self, q_pckt: MsgQueuePacket) -> None:
        """ LRP task indicates that a new record was received. Process the record, store it as an attribute in RDB,
        and message the RAP-CUC
        @param q_pckt: portalId, recordNo, data
        """
        rapp = self.get_partipipant_by_portalid(q_pckt.message["portalId"])
        rapp.deserialize_attribute(q_pckt.message)

    def declare_attribute_request(self, q_pckt: MsgQueuePacket) -> None:
        """ Declare an attribute on behalf of the RAP-CUC. Arranges transmission with LRP task.
        @param q_pckt: participantId and attribute
        """
        rapp = self.get_partipipant_by_id(q_pckt.message["participantId"])
        rapp.declare_attribute(q_pckt.message["attribute"])

    def withdraw_attribute_request(self, q_pckt: MsgQueuePacket) -> None:
        """ Withdraw an attribute on behalf of the RAP-CUC. Arranges transmission with LRP task.
        @param q_pckt: participantId and attribute
        """
        rapp = self.get_partipipant_by_id(q_pckt.message["participantId"])
        rapp.withdraw_attribute(q_pckt.message["attribute"])
