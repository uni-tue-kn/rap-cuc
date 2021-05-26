#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-

import sys
from collections import OrderedDict
from dataclasses import dataclass
import threading
from threading import Event

sys.path.insert(0, '..')
from shared.aux.logger import Logger
from shared.aux.msgQueue import MsgQueue
from shared.aux.msgQueuePacket import MsgQueuePacket
from shared.aux.msgType import MsgType

# Logger
loggerWrapper = Logger(__file__ + ".log")
logger = loggerWrapper.get_logger()


@dataclass
class Task:
    """General task which uses a given state machine to service messages from other tasks"""
    terminate_event = threading.Event()

    def __init__(self, name=""):

        self.name = name
        self.msg_queue = MsgQueue(name, logger)

    def statemachine(self, states: dict, q_pckt: MsgQueuePacket) -> None:
        """
        State machine passes messages according to their type to the specific handler function.

        @param states: Dictionary with form { msgTypes : handlerFunction(q_pckt) , ... }
        @param q_pckt: Message from a message queue.
        @return:
        """

        if q_pckt.msg_type in states.keys():
            logger.info("Passing message to handler")
            states[q_pckt.msg_type](q_pckt)
        else:
            logger.error("Unknown message type!")

    def run(self, lib) -> None:
        """ Main loop of the task, which waits on messages from a queue and processes according to a state machine
        @param lib:
        """
        while not Task.terminate_event.is_set():

            logger.info("Checking for message...")
            q_pckt = self.msg_queue.get_msg(blocking=True)
            logger.info("Message from other task received!")
            self.statemachine(lib.states, q_pckt)

    def run_task_as_thread(self, lib_instance) -> threading.Thread:
        """
        This methods runs the task as a thread. The state machine is defined by the lib_instance
        @param lib_instance: lib instance of the task containing message handlers
        @return:
        """
        logger.info("Starting %s task.. ", self.name)
        t = threading.Thread(target=self.run, args=[lib_instance])
        t.daemon = True
        t.start()
        return t

