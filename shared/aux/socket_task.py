#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-

import sys
from collections import OrderedDict
from dataclasses import dataclass
import threading
from threading import Event


sys.path.insert(0, '..')
from shared.aux.logger import Logger
from shared.aux.task import Task
from shared.aux.pollableQueue import PollableQueue
from shared.aux.msgQueue import MsgQueue
from shared.aux.msgQueuePacket import MsgQueuePacket
from shared.aux.msgType import MsgType

# Logger
loggerWrapper = Logger(__file__ + ".log")
logger = loggerWrapper.get_logger()

@dataclass
class SocketTask(Task):
    """
    Special task which works as a tcp server and serves a message queue for inter-task communication
    """

    def __init__(self, name):
        super().__init__(name=name)

        self.msg_queue = PollableQueue(self.name, logger)

    def run(self, states: dict) -> None:
        """ Main loop of the task, which waits on messages from a queue and processes according to a state machine
        @param states:
        """
        while not Task.terminate_event.is_set():

            logger.info("Checking for message...")
            # todo replace get_message call with selector based polling with sockets
            q_pckt = self.msg_queue.get_msg(blocking=True)
            logger.info("Message from other task received!")
            self.statemachine(states, q_pckt)

    # todo implement socket handling
    # todo
    # hier wird noch eine liste der sockets benötigt die mit dem Selector überwacht werden.
    # Die sockets werden vom lrp_dummy_lib in die gemeinsame liste eingefügt,
    # wenn ein local target port req empfangen wird
