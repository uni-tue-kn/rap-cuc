#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import json
import copy
from collections import OrderedDict
from dataclasses import dataclass, field

from .lrp_dummy_lib import LrpDummy
from .rap_participant import RapParticipantSM
from stream_management.lib.stream_status_db import StreamState

sys.path.insert(0, '..')
from shared.aux.msgQueue import MsgQueue
from shared.aux.pollableQueue import PollableQueue
from shared.aux.msgQueuePacket import MsgQueuePacket
from shared.aux.msgType import MsgType
from shared.aux.task import Task
from shared.aux.socket_task import SocketTask
from shared.aux.logger import Logger
from shared.qcc.tsn_types import Talker
from shared.qcc.tsn_types import Listener
from shared.rap.TAA import TAA
from shared.rap.LAA import LAA
from shared.rap.Listener_status import Listener_status
from shared.qcc.tsn_types import StatusStream, StatusTalkerListener

# Logger
loggerWrapper = Logger(__file__ + ".log")
logger = loggerWrapper.get_logger()

@dataclass()
class StreamRegister:
    stream_register: dict = field(default_factory=dict)

    def register_talker(self, stream_id, participant_id, attribute):
        if not self.stream_register.get(stream_id):
            self.stream_register[stream_id] = {}
        self.stream_register[stream_id]["talker"] = participant_id
        self.stream_register[stream_id]["talker_attribute"] = attribute

    def register_listener(self, stream_id, participant_id):
        if not self.stream_register.get(stream_id):
            self.stream_register[stream_id] = {}
        if not self.stream_register[stream_id].get("listeners"):
            self.stream_register[stream_id]["listeners"] = []
            if participant_id not in self.stream_register[stream_id].get("listeners"):
                self.stream_register[stream_id]["listeners"].append(participant_id)

    def deregister_talker(self, stream_id):
        self.stream_register[stream_id].pop("talker")
        self.stream_register[stream_id].pop("talker_attribute")

    def deregister_listener(self, stream_id, participant_id):
        self.stream_register[stream_id]["listeners"].remove(participant_id)

    def get_participant_id_talker(self, stream_id):
        if self.stream_register.get(stream_id):
            return self.stream_register.get(stream_id).get("talker")
        return -1  # Participant Id is always positive

    def get_participant_id_listeners(self, stream_id):
        if self.stream_register.get(stream_id):
            if self.stream_register.get(stream_id).get("listeners"):
                return self.stream_register.get(stream_id).get("listeners")
        return []

    def get_talker_attribute(self, stream_id):
        attr = self.stream_register[stream_id]["talker_attribute"]
        return copy.deepcopy(attr)


@dataclass
class RapCucSM:

    def __init__(self, queue_register: dict):
        self.queue_register = queue_register

        # State machine of the corresponding task
        # Includes a mapping from msgTypes to handler function to serve requests/indications from other tasks
        self.states = {
            MsgType.RPSI_REGISTER_IND: self.register_attribute,
            MsgType.RPSI_DEREGISTER_IND: self.deregister_attribute,
            MsgType.SM_STREAM_STATUS_IND: self.process_stream_status_update,
        }

        """ Create Sub-Tasks  """
        self.lrp_task = SocketTask("lrp_dummy")
        self.rap_participant_task = Task("rap_participants")

        """ Register Message Queues """
        self.queue_register[self.lrp_task.name] = self.lrp_task.msg_queue
        self.queue_register[self.rap_participant_task.name] = self.rap_participant_task.msg_queue

        """ Initialize Task Libraries"""
        self.lrp_dummy_lib = LrpDummy(self.queue_register)
        self.rap_participant_lib = RapParticipantSM(self.queue_register)

        """ Run Subtasks """
        self.lrp_task.run_task_as_thread(self.lrp_dummy_lib)
        self.rap_participant_task.run_task_as_thread(self.rap_participant_lib)

        localTargetPortInfo = open(
            os.path.dirname(os.path.realpath('__file__')) + "/protocol_connector/localTargetPortInfo.json").read()
        targetPortInfo = json.loads(localTargetPortInfo)

        self.neighbourTargetPortList = targetPortInfo["neighbourTargetPorts"]
        self.localTargetPortList = targetPortInfo["localTargetPorts"]

        self.stream_register = StreamRegister()

    def register_attribute(self, q_pckt: MsgQueuePacket) -> None:
        """
        Process the registered RAP attribute of a peer received by a RAP participant
        @param q_pckt: participantId and inAttribute
        """
        attribute = q_pckt.message["attribute"]
        participantId = q_pckt.message["participantId"]
        msg = None
        msg_type = None
        stream_id = attribute.get_stream_id()

        # TAA
        if 0x01 == attribute.get_type():
            msg_type = MsgType.PC_REG_TALKER_REQUIREMENT_IND
            talker = self.build_qcc_talker(attribute)
            msg = {
                "stream_id": stream_id,
                "mac": attribute.get_mac(),
                "talker": talker
            }
            self.stream_register.register_talker(stream_id, participantId, attribute)
        # LAA
        elif 0x02 == attribute.get_type():
            msg_type = MsgType.PC_REG_LISTENER_REQUIREMENT_IND

            # Listener MAC is not contained in LAA, thus is extracted from static config
            mac = self.get_listener_mac(participantId)
            if mac == "":
                return
            # Built listener group
            data = {
                    "index": 0,
                    "end-station-interfaces": [
                        {
                            "mac-address": mac,
                            "interface-name": ""
                        }
                    ]
                }
            msg = {
                "stream_id": stream_id,
                "mac": mac,
                "listener": Listener(data)
            }
            self.stream_register.register_listener(stream_id, participantId)

        if msg is not None and msg_type is not None:
            self.queue_register["stream_management"].send_msg(msg=MsgQueuePacket(msg_type, msg),
                                                         sender_name="rap_cuc")

    def build_qcc_talker(self, attribute):
        data = {
            "stream-rank": {"rank": attribute.stream_rank},
            "end-station-interfaces": [
                {
                    "mac-address": attribute.get_mac(),
                    "interface-name": ""
                }
            ],
            "data-frame-specification": [
                {
                    "index": 0,
                    "field": {
                        "ieee802-mac-addresses": {
                            "destination-mac-address": attribute.get_dst_mac(),
                            "source-mac-address": attribute.get_mac()
                        }
                    }
                },
                {
                    "index": 1,
                    "field": {
                        "ieee802-vlan-tag": {
                            "priority-code-point": attribute.data_frame_parameters_stlv.priority,
                            "vlan-id": attribute.data_frame_parameters_stlv.vlan_id
                        }
                    }
                },
            ],
            "traffic-specification":
                {
                    "interval": {
                        "numerator": attribute.organizationally_defined_stlv.interval_numerator,
                        "denominator": attribute.organizationally_defined_stlv.interval_denominator
                    },
                    "max-frames-per-interval": attribute.msrp_tspec_stlv.max_interval_frames,
                    "max-frame-size": attribute.msrp_tspec_stlv.max_frame_size,
                    "time-aware": {
                        "earliest-transmit-offset": attribute.organizationally_defined_stlv.earliest_transmit_offset,
                        "latest-transmit-offset": attribute.organizationally_defined_stlv.latest_transmit_offset,
                        "jitter": attribute.organizationally_defined_stlv.jitter
                    }
                },
            "user-to-network-requirements": {
                "max-latency": attribute.organizationally_defined_stlv.maximum_latency
            }
        }
        return Talker(data)

    def get_listener_mac(self, participantId):
        portalId = self.rap_participant_lib.get_partipipant_by_id(participantId).portalId
        peer = self.lrp_dummy_lib.get_peer_by_portalId(portalId)
        peer_addr = peer[0]
        peer_port = str(peer[1])
        mac = ""
        for targetPort in self.neighbourTargetPortList:
            if peer_port == targetPort["tcpPort"] and peer_addr == targetPort["addrIPv4"]:
                mac = targetPort["chassisId"]  # We assume that the cassis Id is the mac address
        return mac

    def deregister_attribute(self, q_pckt: MsgQueuePacket) -> None:
        """
        Deregister an RAP attribute on behalf of a RAP participant
        @param q_pckt: attribute
        """
        attribute = q_pckt.message["attribute"]
        participantId = q_pckt.message["participantId"]
        msg = None
        msg_type = None

        # TAA
        if 0x01 == attribute.get_type():
            msg_type = MsgType.PC_DEREG_TALKER_REQUIREMENT_IND
            msg = {
                "stream_id": attribute.get_stream_id(),
                "mac": attribute.get_mac()
            }
            self.stream_register.deregister_talker(attribute.get_stream_id())
        # LAA
        elif 0x02 == attribute.get_type():
            msg_type = MsgType.PC_DEREG_LISTENER_REQUIREMENT_IND
            msg = {
                "stream_id": attribute.get_stream_id(),
                "mac": self.get_listener_mac(participantId)
            }
            self.stream_register.deregister_listener(attribute.get_stream_id(), participantId)

        # todo maybe implement in future:
        #  when an attribute is deregistered, the rap-cuc can withdraw the response it possibly daclared to the host
        #  on successfull or unsuccessful stream reservation.

        if msg is not None and msg_type is not None:
            self.queue_register["stream_management"].send_msg(msg=MsgQueuePacket(msg_type, msg),
                                                             sender_name="rap_cuc")

    def process_stream_status_update(self, q_pckt: MsgQueuePacket) -> None:
        """
        Trigger notifcation of end stations based on the stream status and configuration data handed from SML
        @param q_pckt: status-stream and status-talker-listener groupings
        """
        stream_id: str = q_pckt.message["stream_id"]
        talkers_conf: StatusTalkerListener = q_pckt.message["talker_conf"]
        listeners_config: [StatusTalkerListener] = q_pckt.message["listeners_conf"]
        stream_status: StatusStream = q_pckt.message["stream_status"]
        talker_status = stream_status.statusInfo["talker-status"]
        stream_state = q_pckt.message["stream_state"]

        if stream_state == StreamState.WITHDRAWN:
            self.withdraw_all_attributes(stream_id)
        elif stream_state == StreamState.DEPLOYED or stream_state == StreamState.ERROR:
            self.notify_listeners(listeners_config, stream_id, stream_status, talker_status)
            self.notify_talker(stream_id, stream_status, talkers_conf)

    def withdraw_all_attributes(self, stream_id):
        """ Withdraw the attributes declared for one stream
        @return:
        """
        listeners_part_ids = self.stream_register.get_participant_id_listeners(stream_id)
        talker_participantId = self.stream_register.get_participant_id_talker(stream_id)

        # Withdraw TAA from Listeners
        taa = self.stream_register.get_talker_attribute(stream_id)
        for part_id in listeners_part_ids:
            self.withdraw_attribute(part_id, taa)

        # Withdraw LAA from Listener
        self.withdraw_attribute(talker_participantId, LAA(stream_id=stream_id))

    def notify_listeners(self, listeners_configs: [StatusTalkerListener], stream_id, stream_status, talker_status):
        listeners_part_ids = self.stream_register.get_participant_id_listeners(stream_id)
        # listener_partId_mac = {x: self.get_listener_mac(x) for x in listeners_part_ids}
        listener_partId_mac = {self.get_listener_mac(x): x for x in listeners_part_ids}

        # All successful listeners
        for listener_config in listeners_configs:
            taa = self.stream_register.get_talker_attribute(stream_id)
            taa.accumulated_maximum_latency += listener_config.accumulatedLatency

            mac = listener_config.interfaceConfiguration.interfaceList[0].interfaceId.macAddress

            if talker_status == 2:  # Talker Status= Failed
                taa.add_failure_information(mac=stream_status.failedInterfaces[0].macAddress,
                                            failure_code=stream_status.statusInfo["failure-code"])

            partId = listener_partId_mac.pop(mac)
            self.declare_attribute(participantId=partId, attribute=taa)
        # failed listeners (listeners with no configuration must be failed)
        for l_mac, l_partId in listener_partId_mac:
            taa = self.stream_register.get_talker_attribute(stream_id)
            taa.add_failure_information(mac=stream_status.failedInterfaces[0].macAddress,
                                        failure_code=stream_status.statusInfo["failure-code"])
            self.declare_attribute(participantId=l_partId, attribute=taa)

    def notify_talker(self, stream_id, stream_status, talkers_config):
        laa = LAA(stream_id)
        laa.listener_attach_status = stream_status.statusInfo["listener-status"]
        # Attach failure information if needed
        if laa.listener_attach_status is Listener_status.FAILED \
                or laa.listener_attach_status is Listener_status.PARTIAL_FAILED:
            laa.add_failure_information(mac=stream_status.failedInterfaces[0].macAddress,
                                        failure_code=stream_status.statusInfo["failure-code"])
        # Attach interface configuration if needed
        elif laa.listener_attach_status is Listener_status.READY:
            laa.add_interface_configuration(json.dumps(talkers_config.interfaceConfiguration.interfaceList[0].getData()))
        # Send declaration request to rap participant
        talker_participantId = self.stream_register.get_participant_id_talker(stream_id)
        if talker_participantId != -1:
            self.declare_attribute(participantId=talker_participantId, attribute=laa)
            logger.error("Talker does not Exist!")


    def declare_attribute(self, participantId, attribute):
        msg = {
            "participantId": participantId,
            "attribute": attribute
        }
        self.queue_register["rap_participants"].send_msg(msg=MsgQueuePacket(MsgType.RPSI_DECLARE_REQ, msg),
                                                         sender_name="rap_cuc")

    def withdraw_attribute(self, participantId, attribute):
        msg = {
            "participantId": participantId,
            "attribute": attribute
        }
        self.queue_register["rap_participants"].send_msg(msg=MsgQueuePacket(MsgType.RPSI_WITHDRAW_REQ, msg),
                                                         sender_name="rap_cuc")
