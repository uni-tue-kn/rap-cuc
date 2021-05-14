#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-

import queue
import sys

sys.path.insert(0, '..')

class MsgQueue(queue.Queue):
    """ Message Queue for asynchronously passing messages between tasks"""
    def __init__(self, task_name: str, logger):
        super().__init__(maxsize=15)
        self.task_name = task_name
        self.name = task_name + "_queue"
        self.logger = logger

    def get_msg(self, blocking=True):
        """ Get a message from the queue """
        self.logger.info("%s: %s takes from queue and blocks", self.name, self.task_name)

        try:
            msg = self.get(block=blocking)
            self.logger.info("%s: %s got item from queue and releases ", self.name, self.task_name)

        except queue.Empty:
            self.logger.error("%s: %s reached in an empty queue", self.name, self.task_name)
            return None

        return msg

    def send_msg(self, msg, sender_name):
        """
        Add a new message in the queue
        @param msg:
        @param sender_name:
        @return:
        """
        self.logger.info("%s: %s adds item to queue: %s", self.name, sender_name, msg.message)
        self.put(msg)
        self.logger.info("%s: %s added item to queue", self.name, sender_name)

    def is_empty(self):
        return self.is_empty()
