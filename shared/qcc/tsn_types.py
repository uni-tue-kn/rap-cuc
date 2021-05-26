import os
import json
from dataclasses import dataclass
from abc import ABC, abstractmethod

@dataclass
class InterfaceId:
    macAddress: str
    interfaceName: str
    
    def __init__(self, data):
        self.macAddress = data.get('mac-address')
        self.interfaceName = data.get('interface-name')
    
    def getData(self):
        return {
            "mac-address": self.macAddress,
            "interface-name": self.interfaceName
        }
     
@dataclass
class InterfaceConfigurationListConfig:
    index: int
    
    def __init__(self, data):
        self.index = data.get("index")
    
    def getData(self):
        return {
            "index" : self.index
        }
        
    @staticmethod
    def factory(data):
        if "ieee802-mac-addresses" in data:
            return IeeeMacAddresses(data)
        if "ieee802-vlan-tag" in data:
            return IeeeVlanTag(data)
        if "ipv4-tuple" in data:
            return Ipv4Tuple(data)
        if "ipv6-tuple" in data:
            return Ipv6Tuple(data)
        if "time-aware-offset" in data:
            return TimeAwareOffset(data)
        return None
        
@dataclass  
class IeeeMacAddresses(InterfaceConfigurationListConfig):
    destinationMacAddress: str
    sourceMacAddress: str
    
    def __init__(self, data):
        super().__init__(data)
        self.destinationMacAddress = data["ieee802-mac-addresses"].get("destination-mac-address")
        self.sourceMacAddress = data["ieee802-mac-addresses"].get("source-mac-address")
    
    def getData(self):
        out = super().getData()
        out["ieee802-mac-addresses"] = {
            "destination-mac-address": self.destinationMacAddress,
            "source-mac-address": self.sourceMacAddress,
        }
        return out
       
@dataclass 
class IeeeVlanTag(InterfaceConfigurationListConfig):
    priorityCodePoint: int
    vlanId: int
    
    def __init__(self, data):
        super().__init__(data)
        self.priorityCodePoint = data["ieee802-vlan-tag"].get("priority-code-point")
        self.vlanId = data["ieee802-vlan-tag"].get("vlan-id")
    
    def getData(self):
        out = super().getData()
        out["ieee802-vlan-tag"] = {
            "priority-code-point": self.priorityCodePoint,
            "vlan-id": self.vlanId,
        }
        return out
        
@dataclass  
class Ipv4Tuple(InterfaceConfigurationListConfig):
    sourceIpAddress: str
    destinationIpAddress: str
    dscp: int
    protocol: int
    sourcePort: int
    destinationPort: int
    
    def __init__(self, data):
        super().__init__(data)
        self.sourceIpAddress = data["ipv4-tuple"].get("source-ip-address")
        self.destinationIpAddress = data["ipv4-tuple"].get("destination-ip-address")
        self.dscp = data["ipv4-tuple"].get("dscp")
        self.protocol = data["ipv4-tuple"].get("protocol")
        self.sourcePort = data["ipv4-tuple"].get("source-port")
        self.destinationPort = data["ipv4-tuple"].get("destination-port")
    
    def getData(self):
        out = super().getData()
        out["ipv4-tuple"] = {
            "source-ip-address": self.sourceIpAddress,
            "destination-ip-address": self.destinationIpAddress,
            "dscp": self.dscp,
            "protocol": self.protocol,
            "source-port": self.sourcePort,
            "destination-port": self.destinationPort,
        }
        return out
        
@dataclass  
class Ipv6Tuple(InterfaceConfigurationListConfig):
    sourceIpAddress: str
    destinationIpAddress: str
    dscp: int
    protocol: int
    sourcePort: int
    destinationPort: int
    
    def __init__(self, data):
        super().__init__(data)
        self.sourceIpAddress = data["ipv6-tuple"].get("source-ip-address")
        self.destinationIpAddress = data["ipv6-tuple"].get("destination-ip-address")
        self.dscp = data["ipv6-tuple"].get("dscp")
        self.protocol = data["ipv6-tuple"].get("protocol")
        self.sourcePort = data["ipv6-tuple"].get("source-port")
        self.destinationPort = data["ipv6-tuple"].get("destination-port")
    
    def getData(self):
        out = super().getData()
        out["ipv6-tuple"] = {
            "source-ip-address": self.sourceIpAddress,
            "destination-ip-address": self.destinationIpAddress,
            "dscp": self.dscp,
            "protocol": self.protocol,
            "source-port": self.sourcePort,
            "destination-port": self.destinationPort,
        }
        return out
        
@dataclass  
class TimeAwareOffset(InterfaceConfigurationListConfig):
    offset: int 
    
    def __init__(self, data):
        super().__init__(data)
        self.offset = data["time-aware-offset"]
    
    def getData(self):
        out = super().getData()
        out["time-aware-offset"] = self.offset
        return out
       
@dataclass
class InterfaceConfigurationList:
    interfaceId: InterfaceId
    configList: [InterfaceConfigurationListConfig]
    
    def __init__(self, data):
        self.interfaceId = InterfaceId(data)
        self.configList = [InterfaceConfigurationListConfig.factory(x) for x in data.get("config-list", [])]
        
    def getData(self):
        out = self.interfaceId.getData()
        out['config-list'] = [x.getData() for x in self.configList]
        return out
        
@dataclass
class InterfaceConfiguration:
    interfaceList: [InterfaceConfigurationList]
    
    def __init__(self, data):
        self.interfaceList = [InterfaceConfigurationList(x) for x in data.get("interface-list", [])]
        
    def getData(self):
        return {
            "interface-list": [x.getData() for x in self.interfaceList]
        }

@dataclass
class TalkerDataFrame:
    index: int
    field: InterfaceConfigurationListConfig
    
    def __init__(self, data):
        self.index = data.get("index")
        self.field = InterfaceConfigurationListConfig.factory(data.get("field", {}))
    
    def getData(self):
        return {
            "index" : self.index,
            "field" : self.field.getData()            
        }
 
@dataclass
class Talker:
    streamRank: int
    endStationInterfaces: [InterfaceId]
    dataFrameSpecification: [TalkerDataFrame]
    intervalNumerator: int
    intervalDenominator: int
    maxFramesPerInterval: int
    maxFrameSize: int
    transmissionSelection: int
    timeAware: dict
    numSeamlessTrees: int
    maxLatency: int
    vlanTagCapable: bool
    cbStreamIdenTypeList: int
    cbSequenceTypeList: int
    
    def __init__(self, data):
        self.streamRank = data.get("stream-rank", {}).get("rank")
        self.endStationInterfaces = [InterfaceId(x) for x in data.get("end-station-interfaces", [])]
        self.dataFrameSpecification = [TalkerDataFrame(x) for x in data.get("data-frame-specification", [])]
        self.intervalNumerator = data.get("traffic-specification", {}).get("interval", {}).get("numerator")
        self.intervalDenominator = data.get("traffic-specification", {}).get("interval", {}).get("denominator")
        self.maxFramesPerInterval = data.get("traffic-specification", {}).get("max-frames-per-interval")
        self.maxFrameSize = data.get("traffic-specification", {}).get("max-frame-size")
        self.transmissionSelection = data.get("traffic-specification", {}).get("transmission-selection")
        self.timeAware = {
            "earliest-transmit-offset" : data.get("traffic-specification", {})["time-aware"].get("earliest-transmit-offset"),
            "latest-transmit-offset" : data.get("traffic-specification", {})["time-aware"].get("latest-transmit-offset"),
            "jitter" : data.get("traffic-specification", {})["time-aware"].get("jitter")
        } if "time-aware" in data.get("traffic-specification", {}) else None
        self.numSeamlessTrees = data.get("user-to-network-requirements", {}).get("num-seamless-trees", 1)
        self.maxLatency = data.get("user-to-network-requirements", {}).get("max-latency", 0)
        self.vlanTagCapable = data.get("interface-capabilities", {}).get("vlan-tag-capable", False)
        self.cbStreamIdenTypeList = data.get("interface-capabilities", {}).get("cb-stream-iden-type-list")
        self.cbSequenceTypeList = data.get("interface-capabilities", {}).get("cb-sequence-type-list")
    
    def getData(self):
        return {
            "stream-rank" : { "rank" : self.streamRank },
            "end-station-interfaces" : [x.getData() for x in self.endStationInterfaces],
            "data-frame-specification" : [x.getData() for x in self.dataFrameSpecification],
            "traffic-specification" : {
                "interval" : {
                    "numerator" : self.intervalNumerator,
                    "denominator" : self.intervalDenominator
                },
                "max-frames-per-interval" : self.maxFramesPerInterval,
                "max-frame-size" : self.maxFrameSize,
                "transmission-selection" : self.transmissionSelection,
                "time-aware" : self.timeAware
            },
            "user-to-network-requirements" : {
                "num-seamless-trees" : self.numSeamlessTrees,
                "max-latency" : self.maxLatency
            },
            "interface-capabilities" : {
                "vlan-tag-capable" : self.vlanTagCapable,
                "cb-stream-iden-type-list" : self.cbStreamIdenTypeList,
                "cb-sequence-type-list" : self.cbSequenceTypeList
            }
        }
    
@dataclass
class Listener:
    index: int
    endStationInterfaces: [InterfaceId]
    numSeamlessTrees: int
    maxLatency: int
    vlanTagCapable: bool
    cbStreamIdenTypeList: int
    cbSequenceTypeList: int
    
    def __init__(self, data):
        self.index = data.get("index")
        self.endStationInterfaces = [InterfaceId(x) for x in data.get("end-station-interfaces", [])]
        self.numSeamlessTrees = data.get("user-to-network-requirements", {}).get("num-seamless-trees", 1)
        self.maxLatency = data.get("user-to-network-requirements", {}).get("max-latency", 0)
        self.vlanTagCapable = data.get("interface-capabilities", {}).get("vlan-tag-capable", False)
        self.cbStreamIdenTypeList = data.get("interface-capabilities", {}).get("cb-stream-iden-type-list")
        self.cbSequenceTypeList = data.get("interface-capabilities", {}).get("cb-sequence-type-list")
    
    def getData(self):
        out = {
            "end-station-interfaces" : [x.getData() for x in self.endStationInterfaces],
            "user-to-network-requirements" : {
                "num-seamless-trees" : self.numSeamlessTrees,
                "max-latency" : self.maxLatency
            },
            "interface-capabilities" : {
                "vlan-tag-capable" : self.vlanTagCapable,
                "cb-stream-iden-type-list" : self.cbStreamIdenTypeList,
                "cb-sequence-type-list" : self.cbSequenceTypeList
            }         
        }
        if self.index is not None:
            out["index"] = self.index
        return out


@dataclass
class StatusTalkerListener:
    index: int
    accumulatedLatency: int
    interfaceConfiguration: InterfaceConfiguration
    
    def __init__(self, data):
        self.index = data.get("index")
        self.accumulatedLatency = data.get("accumulated-latency")
        self.interfaceConfiguration = InterfaceConfiguration(data.get("interface-configuration", {}))
    
    def getData(self):
        out = {
            "accumulated-latency": self.accumulatedLatency,
            "interface-configuration": self.interfaceConfiguration.getData()
        }
        if self.index is not None:
            out["index"] = self.index
        return out


@dataclass
class StatusStream:
    statusInfo: {
        "talker-status": 0,
        "listener-status": 0,
        "failure-code": 0
    }
    failedInterfaces: [InterfaceId]
    
    def __init__(self, data):
        self.statusInfo = data.get("status-info", {})
        self.failedInterfaces = [InterfaceId(x) for x in data.get("failed-interfaces", [])]
    
    def getData(self):
        return {
            "status-info": self.statusInfo,
            "failed-interfaces": [x.getData() for x in self.failedInterfaces],
        }

