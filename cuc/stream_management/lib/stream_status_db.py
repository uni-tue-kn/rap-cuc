#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from dataclasses import dataclass, field
from enum import Enum

from shared.qcc.tsn_types import StatusStream
from shared.qcc.tsn_types import StatusTalkerListener
from shared.aux.msgType import MsgType

class StreamState(Enum):
    NEW = 1,
    PENDING = 2,
    DEPLOYED = 3,
    WITHDRAWN = 4,
    ERROR = 5

@dataclass
class StreamStatusDbItem:
    state: StreamState
    status: StatusStream = None
    talkerConfig: StatusTalkerListener = None
    listenerConfigs: [StatusTalkerListener] = field(default_factory=list)


@dataclass
class StreamStatusDb:
    data: dict = field(default_factory=dict)  # stream_id : item

    def is_state(self, stream_id, state: StreamState):
        if self.data.get(stream_id):
            return self.data[stream_id].state == state

        return False

    def add_stream(self, stream_id):
        self.data[stream_id] = StreamStatusDbItem(state=StreamState.NEW)

    def update_stream_state(self, stream_id, state):
        self.data[stream_id].state = state

    def update_talker_conf(self, stream_id, configuration):
        self.data[stream_id].talkerConfig = configuration

    def update_listeners_confs(self, stream_id, configurations):
        self.data[stream_id].listenerConfigs = configurations

    def update_status(self, stream_id, status):
        self.data[stream_id].status = status

    def advance_state(self, event: str, stream_id: str):
        """Advance the state of a stream based on a event
            @param event: str   input event NEW_TALKER, NEW_LISTENER, REM_STREAM, REM_LISTENER, NEW_RESULT
            @param stream_id:
        @return: Returns message type of MsgType.CC_____ requests
        """

        if self.data.get(stream_id):
            curr_state = self.data.get(stream_id).state

            if curr_state == StreamState.WITHDRAWN:
                self.data[stream_id].state = StreamState.NEW
                return None

            if event == "NEW_TALKER":
                if curr_state == StreamState.NEW:
                    self.data[stream_id].state = StreamState.PENDING
                    return MsgType.CC_ADD_STREAM_REQ

            if event == "UDT_TALKER":
                if curr_state != StreamState.NEW:
                    self.data[stream_id].state = StreamState.PENDING
                    return MsgType.CC_UPDATE_STREAM_REQ
                    # todo maybe improve behavior: only retry when talker caused the error

            elif event == "NEW_LISTENER":
                if curr_state == StreamState.NEW:
                    self.data[stream_id].state = StreamState.PENDING
                    return MsgType.CC_ADD_STREAM_REQ
                elif curr_state == StreamState.PENDING:
                    return MsgType.CC_ADD_LISTENER_REQ
                elif curr_state == StreamState.ERROR:
                    self.data[stream_id].state = StreamState.PENDING
                    return MsgType.CC_ADD_LISTENER_REQ

            elif event == "UDT_LISTENER":
                # NEW: do nothing
                if curr_state != StreamState.NEW:
                    self.data[stream_id].state = StreamState.PENDING
                    return MsgType.CC_UPDATE_LISTENER_REQ

            elif event == "REM_STREAM":
                self.data[stream_id].state = StreamState.WITHDRAWN
                return MsgType.CC_REMOVE_STREAM_REQ

            elif event == "REM_STREAM_WITH_REMNANT":
                self.data[stream_id].state = StreamState.NEW
                return MsgType.CC_REMOVE_STREAM_REQ

            elif event == "REM_LISTENER":
                self.data[stream_id].state = StreamState.PENDING
                return MsgType.CC_REM_LISTENER_REQ

            elif event == "NEW_RESULT":
                if curr_state == StreamState.PENDING or curr_state == StreamState.DEPLOYED or curr_state == StreamState.ERROR:
                    if self.data[stream_id].status.statusInfo["failure-code"] == 0:
                        self.data[stream_id].state = StreamState.DEPLOYED
                    else:
                        self.data[stream_id].state = StreamState.ERROR
                return MsgType.SM_STREAM_STATUS_IND
        else:
            # stream is not yet known, so create a NEW stream
            self.add_stream(stream_id)
            return None


