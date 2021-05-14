#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-

class MsgQueuePacket:
    def __init__(self, msg_type, msg):
        self.msg_type = msg_type
        self.message = msg

