#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from collections import OrderedDict
from dataclasses import dataclass

from .lib.stream_req_db import StreamRequirementDb
from .lib.stream_status_db import StreamStatusDb, StreamState

sys.path.insert(0, '..')
from shared.aux.logger import Logger
from shared.aux.msgQueue import MsgQueue
from shared.aux.msgQueuePacket import MsgQueuePacket
from shared.aux.msgType import MsgType

# Logger
loggerWrapper = Logger(__file__ + ".log")
logger = loggerWrapper.get_logger()

class StreamManagementSM:
    """
    The stream management administrates the life-cycle of a stream.
    Tasks:
        - It reacts to new requirements from Protocol Connector
        - It provokes stream reservation/withdrawal via the CNC connector
        - It stores state of all streams and associated configuration data
        - It conveys stream status and configuration data to the the Protocol Connector
    """

    def __init__(self, queue_register: dict):
        self.queue_register = queue_register

        self.srdb = StreamRequirementDb()
        self.ssdb = StreamStatusDb()

        # State machine of the corresponding task
        # Includes a mapping from msgTypes to handler function to serve requests/indications from other tasks
        self.states = {
            MsgType.PC_REG_TALKER_REQUIREMENT_IND: self.register_talker_requirements,
            MsgType.PC_REG_LISTENER_REQUIREMENT_IND: self.register_listener_requirements,
            MsgType.PC_DEREG_TALKER_REQUIREMENT_IND: self.deregister_talker_requirements,
            MsgType.PC_DEREG_LISTENER_REQUIREMENT_IND: self.deregister_listener_requirements,
            MsgType.CC_RESERVATION_RESULT_IND: self.process_reservation_result,
        }


    def register_talker_requirements(self, q_pckt: MsgQueuePacket) -> None:
        """ Register a talkers requirements for stream life cycle management
        @param q_pckt: stream_id, mac, talker
        """
        stream_id = q_pckt.message["stream_id"]
        mac = q_pckt.message["mac"]
        requirement = q_pckt.message["talker"]

        event = self.srdb.add_requirement(stream_id, mac, "talker", requirement)

        msg_type = self.ssdb.advance_state(event, stream_id)

        if msg_type is not None:
            # msg_type = CC_ADD_STREAM_REQ | CC_UPDATE_STREAM_REQ
            msg = {
                "stream_id": stream_id,
                "talker_req": self.srdb.get_talker_by_stream_id(stream_id),
                "listener_reqs": self.srdb.get_listeners_by_stream_id(stream_id)
            }
            self.queue_register["cnc_connector"].send_msg(msg=MsgQueuePacket(msg_type, msg),
                                                              sender_name="sml")

    def register_listener_requirements(self, q_pckt: MsgQueuePacket) -> None:
        """ Register a talkers requirements for stream life cycle management
        @param q_pckt: stream_id, mac, listener
        """
        stream_id = q_pckt.message["stream_id"]
        mac = q_pckt.message["mac"]
        requirement = q_pckt.message["listener"]
        msg = None

        event = self.srdb.add_requirement(stream_id, mac, "listener", requirement)

        msg_type = self.ssdb.advance_state(event, stream_id)

        if msg_type is not None:
            # type = CC_ADD_STREAM_REQ | CC_ADD_LISTENER_REQ | CC_UPDATE_LISTENER_REQ
            if msg_type == MsgType.CC_ADD_STREAM_REQ:
                msg = {
                    "stream_id": stream_id,
                    "talker_req": self.srdb.get_talker_by_stream_id(stream_id),
                    "listener_reqs": self.srdb.get_listeners_by_stream_id(stream_id)
                }
            elif msg_type == MsgType.CC_ADD_LISTENER_REQ or msg_type == MsgType.CC_UPDATE_LISTENER_REQ:
                    msg = {
                        "stream_id": stream_id,
                        "listener_req": requirement
                    }

            self.queue_register["cnc_connector"].send_msg(msg=MsgQueuePacket(msg_type, msg),
                                                          sender_name="sml")

    def deregister_talker_requirements(self, q_pckt: MsgQueuePacket) -> None:
        """ Deregister a talkers requirements for stream life cycle management
        @param q_pckt: talker MAC and Stream ID
        """
        stream_id = q_pckt.message["stream_id"]
        mac = q_pckt.message["mac"]

        self.srdb.remove_requirement(mac, stream_id)

        if not self.ssdb.is_state(stream_id, StreamState.WITHDRAWN):
            listeners = self.srdb.get_listeners_by_stream_id(stream_id)
            if listeners == []:
                msg_type = self.ssdb.advance_state("REM_STREAM", stream_id)
            else:
                msg_type = self.ssdb.advance_state("REM_STREAM_WITH_REMNANT", stream_id)

            # types = CC_REMOVE_STREAM_REQ
            msg = {
                "stream_id": stream_id,
            }
            self.queue_register["cnc_connector"].send_msg(msg=MsgQueuePacket(msg_type, msg),
                                                          sender_name="sml")

    def deregister_listener_requirements(self, q_pckt: MsgQueuePacket) -> None:
        """ Deegister a talkers requirements for stream life cycle management
        @param q_pckt: listener MAC and stream ID
        """
        stream_id = q_pckt.message["stream_id"]
        mac = q_pckt.message["mac"]
        msg_type = None
        msg = None

        self.srdb.remove_requirement(mac, stream_id)

        # check if a listener is left for the stream
        listeners = self.srdb.get_listeners_by_stream_id(stream_id)
        if not self.ssdb.is_state(stream_id, StreamState.WITHDRAWN):
            if listeners == []:
                talker = self.srdb.get_talker_by_stream_id(stream_id)
                if talker is None:
                    msg_type = self.ssdb.advance_state("REM_STREAM", stream_id)
                else:
                    msg_type = self.ssdb.advance_state("REM_STREAM_WITH_REMNANT", stream_id)
            else:
                msg_type = self.ssdb.advance_state("REM_LISTENER", stream_id)

        # types = CC_REM_LISTENER_REQ | CC_REMOVE_STREAM_REQ
        if msg_type == MsgType.CC_REM_LISTENER_REQ:
            msg = {
                "stream_id": stream_id,
                "listener_mac": mac
            }
        elif msg_type == MsgType.CC_REMOVE_STREAM_REQ:
            msg = {
                "stream_id": stream_id,
            }
        self.queue_register["cnc_connector"].send_msg(msg=MsgQueuePacket(msg_type, msg),
                                                      sender_name="sml")

    def process_reservation_result(self, q_pckt: MsgQueuePacket) -> None:
        """ Process the result of a reservation procedure
        @param q_pckt: stream_id, talker_conf: StatusTalkerListener, listeners_conf: [StatusTalkerListener, ...], stream_status: StatusStream
        """
        stream_id = q_pckt.message["stream_id"]
        talkers_status = q_pckt.message["talker_conf"]
        listeners_status = q_pckt.message["listeners_conf"]
        stream_status = q_pckt.message["stream_status"]

        self.ssdb.update_status(stream_id, stream_status)
        self.ssdb.update_talker_conf(stream_id, talkers_status)
        self.ssdb.update_listeners_confs(stream_id, listeners_status)

        msg_type = self.ssdb.advance_state("NEW_RESULT", stream_id)
        # msg_type: SM_STREAM_STATUS_IND

        q_pckt.message["stream_state"] = self.ssdb.data.get(stream_id).state
        msg = q_pckt.message
        self.queue_register["protocol_connector"].send_msg(msg=MsgQueuePacket(msg_type, msg),
                                                      sender_name="sml")
