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


@dataclass
class LrpDummy:
    """
    This LrpDummy implements the interface of real LRP but does not perform specified LRP signalling
    It provides a listening socket to end stations which can connect to it via TCP
    """

    def __init__(self, queue_register: dict):
        self.queue_register = queue_register

        # State machine of the corresponding task
        # Includes a mapping from msgTypes to handler function to serve requests/indications from other tasks
        self.states = {
        }

    def associate_portal(self, q_pckt: MsgQueuePacket) -> None:
        """ Associate Portal request for portal creation
        @param q_pckt: portalId, associationAllowed: Bool
        """
        pass

    def write_record(self, q_pckt: MsgQueuePacket) -> None:
        """ Serve a write request from LRP application layer
        @param q_pckt: portalId, recordNo, data
        """
        pass

    def delete_record(self, q_pckt: MsgQueuePacket) -> None:
        """ delete a record on behalf of LRP application layer
        @param q_pckt: portalId, recordNo
        """
        pass

    def local_target_port_request(self, q_pckt: MsgQueuePacket) -> None:
        """ Create local portal
        @param q_pckt: localTargetPortReq
        """
        # todo open listening socket ready to accept a connection according to specified address, port

        pass

    def neighbour_target_port_request(self, q_pckt: MsgQueuePacket) -> None:
        """ Create neighbour portal
        @param q_pckt: neighbourTargetPortReq
        """
        # todo open connection with peer at specified address, port

        pass





