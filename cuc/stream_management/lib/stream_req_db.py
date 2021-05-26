#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from dataclasses import dataclass, field

@dataclass
class StreamRequirementDbItem:
    type: str   # "talker"/"listener"
    requirements: object  # Talker or Listener object containing requirements


@dataclass
class StreamRequirementDb:
    data: dict = field(default_factory=dict)  # mac : {stream_id: StreamRequirementDbItem, ...}

    def add_requirement(self, stream_id, mac, type: str, requirements):
        event = "NEW"
        if not self.data.get(mac):
            self.data[mac] = {}

        if self.data.get(mac).get(stream_id):
            event = "UDT"
        self.data[mac][stream_id] = StreamRequirementDbItem(type, requirements)

        return event + "_" + type.upper()

    def remove_requirement(self, mac, stream_id):
        if self.data.get(mac):
            if self.data[mac].get(stream_id):
                return self.data[mac].pop(stream_id)

    def get_talker_by_stream_id(self, stream_id):
        for mac, item in self.data.items():
            for key in item.keys():
                if key == stream_id:
                    if self.data[mac][key].type == "talker":
                        return self.data[mac][key].requirements
        return None

    def get_listeners_by_stream_id(self, stream_id):
        listeners = []
        for mac, item in self.data.items():
            for key in item.keys():
                if key == stream_id:
                    if self.data[mac][key].type == "listener":
                        listeners.append(self.data[mac][key].requirements)
        return listeners

    def get_endstations_by_stream_id(self, stream_id):
        talker = self.get_talker_by_stream_id(stream_id)
        listenerList = self.get_listeners_by_stream_id(stream_id)
        return talker, listenerList