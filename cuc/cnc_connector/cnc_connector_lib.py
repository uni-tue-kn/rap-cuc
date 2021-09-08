#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-

import sys
from collections import OrderedDict
from dataclasses import dataclass

from .webhook_lib import WebhookHandler

sys.path.insert(0, '..')
from shared.aux.logger import Logger
from shared.aux.msgQueuePacket import MsgQueuePacket
from shared.aux.msgType import MsgType

# Logger
loggerWrapper = Logger(__file__ + ".log")
logger = loggerWrapper.get_logger()


@dataclass
class CncConnectorDummySM:
    """
    The CNC Connector is used to handle communication with a CNC
    It receives orders from the SM and hands over results to it
    A subscription based result propagation scheme is supported in combination with the webhook handler
    (see. self.process_cnc_result)
    """

    def __init__(self, queue_register: dict):
        self.queue_register = queue_register

        # State machine of the corresponding task
        # Includes a mapping from msgTypes to handler function to serve requests/indications from other tasks
        self.states = {
            MsgType.CC_ADD_STREAM_REQ: self.add_stream,
            MsgType.CC_UPDATE_STREAM_REQ: self.update_stream,
            MsgType.CC_REMOVE_STREAM_REQ: self.remove_stream,
            MsgType.CC_ADD_LISTENER_REQ: self.add_listener,
            MsgType.CC_REM_LISTENER_REQ: self.remove_listener,
            MsgType.CC_UPDATE_LISTENER_REQ: self.update_listener,
            MsgType.WHH_RESULT_IND: self.process_cnc_result,
        }

        self.wh_handler = WebhookHandler(self.queue_register)
        """ The Webhook Handler
         The wh handler can be used to obtain hook ids for requests
            - wh_handler.generate_hook_id
         This hook id can be used as a response callback for long computations, 
         if the cnc supports this mechanism
        """

    def get_states(self) -> dict:
        """ Used to obtain the states to handler function mapping of a state machine for a task
        @return: sates of the statemachine
        """
        return self.states

    def add_stream(self, q_pckt: MsgQueuePacket) -> None:
        """ Initiate the resource reservation process with a CNC
        @param q_pckt: Talker-groupings and Listener-groupings
        @return:
        """

        pass

    def update_stream(self, q_pckt: MsgQueuePacket) -> None:
        """ This handler updates the stream requirements of a stream, as a whole or when talker is updated
        @param q_pckt: Talker-groupings and Listener-groupings
        @return: 
        """
        pass

    def remove_stream(self, q_pckt: MsgQueuePacket) -> None:
        """ Withdraw the reservation of a stream from CNC
        @param q_pckt: contains Stream ID
        @return:
        """
        pass

    def add_listener(self, q_pckt: MsgQueuePacket) -> None:
        """ Make the CNC add a listener to a stream
        @param q_pckt: contains the listener-grouping and stream ID
        @return:
        """
        pass

    def update_listener(self, q_pckt: MsgQueuePacket) -> None:
        """ This handler updates the requirements of a listener to a stream.
        @param q_pckt: contains the listener-grouping and stream ID
        @return:
        """
        pass

    def remove_listener(self, q_pckt: MsgQueuePacket) -> None:
        """ Make the CNC remove a listener from a stream
        @param q_pckt: contains at least the stream ID and the listener's MAC address
        @return:
        """
        pass

    def process_cnc_result(self, q_pckt: MsgQueuePacket) -> None:
        """ Process the subscribed result of a computation passed from WHH
        @param q_pckt:  contains the result from CNC (talker-listener status, stream status)
                        and the callback address of the request
        @return:
        """
        # Parse the result
        # Build message for SML
        # Send to SML message containing:
        # - stream_id,
        # - talker_conf: StatusTalkerListener,
        # - listeners_conf: [StatusTalkerListener, ...],
        # - stream_status: StatusStream
        #msg = {
        #    "stream_id": ,
        #    "talker_conf":,
        #    "listener_conf":,
        #    "stream_status":
        #}

        #self.queue_register["stream_management"].send_msg(msg=MsgQueuePacket(MsgType.CC_RESERVATION_RESULT_IND, msg),
        #                                              sender_name="sml")
        pass

