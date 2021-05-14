#!/usr/bin/env python3
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
        @param q_pckt: talker-grouping
        """
        pass

    def register_listener_requirements(self, q_pckt: MsgQueuePacket) -> None:
        """ Register a talkers requirements for stream life cycle management
        @param q_pckt: listener-grouping
        """
        pass

    def deregister_talker_requirements(self, q_pckt: MsgQueuePacket) -> None:
        """ Deregister a talkers requirements for stream life cycle management
        @param q_pckt: talker MAC and Stream ID
        """
        pass

    def deregister_listener_requirements(self, q_pckt: MsgQueuePacket) -> None:
        """ Deegister a talkers requirements for stream life cycle management
        @param q_pckt: listener MAC and stream ID
        """
        pass

    def process_reservation_result(self, q_pckt: MsgQueuePacket) -> None:
        """ Process the result of a reservation procedure
        @param q_pckt: status-talker-listener groupings, status-stream grouping
        """