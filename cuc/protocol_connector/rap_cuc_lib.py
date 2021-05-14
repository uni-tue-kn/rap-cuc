#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from collections import OrderedDict
from dataclasses import dataclass

from .lrp_dummy_lib import LrpDummy
from .rap_participant import RapParticipantSM

sys.path.insert(0, '..')
from shared.aux.msgQueue import MsgQueue
from shared.aux.pollableQueue import PollableQueue
from shared.aux.msgQueuePacket import MsgQueuePacket
from shared.aux.msgType import MsgType
from shared.aux.task import Task
from shared.aux.socket_task import SocketTask
from shared.aux.logger import Logger

# Logger
loggerWrapper = Logger(__file__ + ".log")
logger = loggerWrapper.get_logger()


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
        pass

        # special queue for compatibility with sockets and selectors
        lrp_task_queue = PollableQueue("lrp_dummy", logger)

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

    def register_attribute(self, q_pckt: MsgQueuePacket) -> None:
        """
        Process the registered RAP attribute of a peer received by a RAP participant
        @param q_pckt:
        """

    def deregister_attribute(self, q_pckt: MsgQueuePacket) -> None:
        """
        Deregister an RAP attribute on behalf of a RAP participant
        @param q_pckt:
        """

    def process_stream_status_update(self, q_pckt: MsgQueuePacket) -> None:
        """
        Trigger notifcation of end stations based on the stream status and configuration data handed from SML
        @param q_pckt: status-stream and status-talker-listener groupings
        """
