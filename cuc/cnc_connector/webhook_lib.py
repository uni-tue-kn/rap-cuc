#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-

import threading
from flask import Flask, request, jsonify, make_response, abort

from shared.aux.msgType import MsgType
from shared.aux.msgQueuePacket import MsgQueuePacket


app = Flask(__name__)


@app.route("/hook/<hook_id>", methods=['POST'])
def main(hook_id):
    data = request.json

    # Hook id known
    if int(hook_id) not in WebhookHandler.hook_ids:
        return make_response({"status": "Unknown hook id"}, 404)

    # hook id known
    WebhookHandler.loose_hook(int(hook_id), data)
    return make_response({"status": "success"}, 200)


class WebhookHandler:
    hook_ids = []
    queue_register = {}

    def __init__(self, queue_register: dict):
        self.currentId = 0
        self.queue_register = queue_register
        WebhookHandler.set_queue_register(queue_register)

        self.states = {
            MsgType.WHH_GET_HOOK_ADDR_REQ: self.generate_hookid
        }

        threading.Thread(target=app.run).start()

    @classmethod
    def set_queue_register(cls, queue_register):
        cls.queue_register = queue_register

    @classmethod
    def loose_hook(cls, hook_id, data):
        cls.hook_ids.remove(hook_id)
        msg = {
            "hook_id": hook_id,
            "result": data
        }
        cls.queue_register["cnc_connector"].send_msg(msg=MsgQueuePacket(MsgType.WHH_RESULT_IND, msg),
                                                            sender_name="sml")

    def generate_hookid(self):
        self.hook_ids.append(self.currentId)
        self.currentId += 1
