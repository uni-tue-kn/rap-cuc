#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import socket
import selectors
from collections import OrderedDict
from dataclasses import dataclass

sys.path.insert(0, '..')
from shared.aux.logger import Logger
from shared.aux.msgQueue import MsgQueue
from shared.aux.msgQueuePacket import MsgQueuePacket
from shared.aux.msgType import MsgType

# Logger
loggerWrapper = Logger(__file__ + ".log")
logger = loggerWrapper.get_logger()


@dataclass
class LrpDummy:
    """
    This LrpDummy implements the interface of real LRP but does not perform specified LRP signalling
    It provides a listening socket to end stations which can connect to it via TCP
    """

    def __init__(self, queue_register: dict):
        self.queue_register = queue_register
        self.name = "lrp_dummy"
        # State machine of the corresponding task
        # Includes a mapping from msgTypes to handler function to serve requests/indications from other tasks
        self.states = {
            MsgType.LRP_LOCAL_TARGET_PORT_REQ: self.local_target_port_request,
            MsgType.LRP_NEIGHBOUR_TARGET_PORT_REQ: self.neighbour_target_port_request,
            MsgType.LRP_ASSOCIATE_PORTAL_REQ: self.associate_portal,
            MsgType.LRP_WRITE_RECORD_REQ: self.write_record,
            MsgType.LRP_DELETE_RECORD_REQ: self.delete_record
        }

        self.socketParticipantMapping = {}  # "socketFileNo" : ParticipantId
        self.portalIdtoSocketMapping = {}  # "portalId" : socket

        self.applicant_db = OrderedDict()  # "portalId": [record to send 1, ...]

        self.selector = selectors.DefaultSelector()

    def get_peer_by_portalId(self, portalId):
        con = self.portalIdtoSocketMapping.get(portalId)
        if con is not None:
            return con.getpeername()

    def associate_portal(self, q_pckt: MsgQueuePacket) -> None:
        """ Associate Portal request for portal creation
        @param q_pckt: portalId, associationAllowed: Bool
        """
        # todo for real lrp implementation:
        # This part would check if the portal is allowed by the rap participant
        # if yes, send the HelloLRPDU(hsConnecting) to the end station via the portals socket
        # if no, send error and terminate connection

        # to fake lrp we send a successful portal status indication to
        msg = {
            "portalId": q_pckt.message["portalId"],
            "associationStatus": "connected",
            "NeighborRegistrarDatabaseOverflow": False
        }
        self.queue_register["rap_participants"].send_msg(MsgQueuePacket(MsgType.LRP_PORTAL_STATUS_IND, msg), self.name)

    def write_record(self, q_pckt: MsgQueuePacket) -> None:
        """ Serve a write request from LRP application layer
        @param q_pckt: portalId, recordNo, data
        """
        portal_id = q_pckt.message["portalId"]

        data = bytearray([q_pckt.message["recordNo"]]) + q_pckt.message["data"]
        self.applicant_db[portal_id].append(data)

        # Activate write event selector for the right socket
        con = self.portalIdtoSocketMapping[portal_id]
        self.selector.modify(con, selectors.EVENT_READ | selectors.EVENT_WRITE, self.handle_connection)

    def delete_record(self, q_pckt: MsgQueuePacket) -> None:
        """ delete a record on behalf of LRP application layer
        @param q_pckt: portalId, recordNo
        """
        pass

    def local_target_port_request(self, q_pckt: MsgQueuePacket) -> None:
        """ Create local portal
        @param q_pckt: localTargetPortReq
        """

        participant_id = q_pckt.message["participantId"]
        appId = q_pckt.message["appId"]
        localTargetPortInfo = q_pckt.message["localTargetPortInfo"]
        helloTime = q_pckt.message["helloTime"]
        appInfo = q_pckt.message["applicationInformation"]
        timeReset = q_pckt.message["cplCompleteListTimerReset"]

        tcpPort = localTargetPortInfo["tcpPort"]
        addrIPv4 = localTargetPortInfo["addrIPv4"]

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setblocking(False)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((addrIPv4, int(tcpPort)))
        sock.listen()

        self.socketParticipantMapping[str(sock.fileno())] = participant_id

        self.selector.register(sock, selectors.EVENT_READ | selectors.EVENT_WRITE, self.accept)

    def neighbour_target_port_request(self, q_pckt: MsgQueuePacket) -> None:
        """ Create neighbour portal
        @param q_pckt: neighbourTargetPortReq
        """
        # todo open connection with peer at specified address, port
        pass

    def accept(self, sock, mask):
        new_connection, addr = sock.accept()
        new_connection.setblocking(True)
        portal_id = str(new_connection.fileno())

        self.portalIdtoSocketMapping[portal_id] = new_connection
        self.applicant_db[portal_id] = []

        #  todo for real lrp implementation: delete this part. This has to be done in the read() then
        msg = {
            "portalId": portal_id,
            "helloLrpdu": None,
            "participantId": self.socketParticipantMapping[str(sock.fileno())]
        }
        self.queue_register["rap_participants"].send_msg(MsgQueuePacket(MsgType.LRP_FIRST_HELLO_IND, msg), self.name)

        self.selector.register(new_connection, selectors.EVENT_READ, self.handle_connection)

    def write(self, con, mask):
        """ Writes record data to the peers.
            A declaration of an attribute is done by sending the whole record
            A withdrawal of an attribute is done by sending the record number with 3 succeeding bytes of zero
            (This makes recite of data easier since header (recordNo, type, length) is always 4 bytes)
        @param con: scoket object
        @param mask: socket event mask
        """
        portal_id = str(con.fileno())

        for index in range(len(self.applicant_db[portal_id])):
            logger.info("Sending data to %s for portal id: %s", con.getpeername(), portal_id)
            data = self.applicant_db[portal_id][index]

            if len(data) == 1:
                data += bytearray(3)

            con.sendall(data)
            self.applicant_db[portal_id].pop(index)

        self.selector.modify(con, selectors.EVENT_READ, self.handle_connection)

    def read(self, connection, mask):
        """ This function handles read events of a selected socket
        @param connection: the socket object
        @param mask: mask containing the events
        """
        """ LRP-Dummy Protocol
            | 0             | 1     | 2   | 3   | 4    ...
            | record_number | type  | length    | values ....

            record_number: Per end station unique record number
            type: type of rap attribute
            length: length of attribute
            values: attribute data contains tlv 

            A declaration of an attribute is done by sending the whole record
            A withdrawal of an attribute is done by sending the record number with 3 succeeding bytes of zero
        """
        header_data = connection.recv(4)
        if header_data == b'':
            return

        record_number = header_data[0]
        attribute_type = header_data[1]
        attribute_length = int.from_bytes(header_data[2:4], signed=False, byteorder='big')
        logger.info("Received record %s from %s", record_number, connection.getpeername())

        if attribute_length > 0:
            data = header_data[1:4] + connection.recv(attribute_length)
            logger.info("data: %s", data)

        else:
            logger.info("%s withdrew attribute with number: %s", connection.getpeername(), record_number)
            data = b''

        msg = {
            "portalId": str(connection.fileno()),
            "recordNo": record_number,
            "data": data
        }
        self.queue_register["rap_participants"].send_msg(MsgQueuePacket(MsgType.LRP_RECORD_WRITTEN_IND, msg), self.name)

    def handle_connection(self, connection, mask):
        if mask & selectors.EVENT_WRITE:
            self.write(connection, mask)
        if mask & selectors.EVENT_READ:
            self.read(connection, mask)
