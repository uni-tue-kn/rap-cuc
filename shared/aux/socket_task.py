#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-

import sys
import selectors
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

        self.lib = None

    def handle_queue(self, connection, mask):
        if mask & selectors.EVENT_READ:

            logger.info("Checking for message...")
            q_pckt = self.msg_queue.get_msg(blocking=True)
            logger.info("Message from other task received!")
            self.statemachine(self.lib.states, q_pckt)

    def statemachine(self, states: dict, q_pckt: MsgQueuePacket) -> None:
        """
        State machine passes messages according to their type to the specific handler function.

        @param states: Dictionary with form { msgTypes : handlerFunction(q_pckt) , ... }
        @param q_pckt: Message from a message queue.
        @return:
        """

        if q_pckt.msg_type in states.keys():
            logger.info("Passing message to handler: %s", q_pckt.msg_type)
            states[q_pckt.msg_type](q_pckt)
        else:
            logger.error("Unknown message type!")

    def run(self, lib) -> None:
        """ Main loop of the task, which waits on messages from a queue and processes according to a state machine
        @param lib: implementation of task, contains states and sockets
        """
        self.lib = lib

        lib.selector.register(self.msg_queue, selectors.EVENT_READ, self.handle_queue)

        while not Task.terminate_event.is_set():
            try:
                while True:
                    for key, mask in lib.selector.select(timeout=None):
                        callback = key.data
                        callback(key.fileobj, mask)

            except KeyboardInterrupt:
                print('Shutting down CUC')
            finally:
                lib.selector.close()


data_to_send = []






