import sys
import argparse
import threading
import time
import concurrent.futures
import enum

#from prompt_toolkit import prompt
#from prompt_toolkit import PromptSession
#from prompt_toolkit.completion import WordCompleter
#from prompt_toolkit import print_formatted_text as print

from protocol_connector.rap_cuc_lib import RapCucSM
from stream_management.sml_lib import StreamManagementSM
from cnc_connector.cnc_connector_lib import CncConnectorDummySM

from shared.aux.msgQueue import MsgQueue
from shared.aux.msgQueuePacket import MsgQueuePacket
from shared.aux.msgType import MsgType


sys.path.insert(0, '..')
from shared.qcc import group_talker
from shared.aux.task import Task
from shared.aux.logger import Logger

loggerWrapper = Logger("cuc.log")
logger = loggerWrapper.get_logger()

def main():
    #logger.info("Parsing arguements")
    #parser = argparse.ArgumentParser(description='RAP endstation prototype:')

    #parser.add_argument('--mac', dest='mac', action='store', default=None, required=True,
    #                    help='mac address of the end station (format: 00-00-00-00-00-00)')
    #parser.add_argument('--cuc-ip', dest='cuc_ip', action='store', default=None, required=True,
    #                    help='ip address of the cuc')
    #parser.add_argument('--cuc-port', dest='cuc_port', action='store', default=None, required=True,
    #                    help='tcp port of the cuc')
    #args = parser.parse_args()
    #mac = args.mac

    app_msg_queue = MsgQueue("cuc_application", logger)
    queue_register = {"cuc_application": app_msg_queue}

    logger.info("Initializing tasks... ")
    protocol_connector_task = init_task("protocol_connector", queue_register)
    sml_task                = init_task("stream_management", queue_register)
    cnc_connector_task      = init_task("cnc_connector", queue_register)
    webhook_task            = init_task("webhook_handler", queue_register)

    logger.info("Initializing libraries... ")
    # protocol connector lib
    pc_lib = RapCucSM(queue_register=queue_register)
    # todo console application wrapper for choosing protocol connector instance
    sml_lib = StreamManagementSM(queue_register=queue_register)
    cnc_connector_lib = CncConnectorDummySM(queue_register=queue_register)
    # todo console application wrapper for choosing cnc connector instance

    """ Startup Tasks as threads """
    terminate_event = threading.Event()
    pc_lib = protocol_connector_task.run_task_as_thread(pc_lib)
    cnc_connector_thread = cnc_connector_task.run_task_as_thread(cnc_connector_lib)
    sml_thread = sml_task.run_task_as_thread(sml_lib)

    # Send Test Message
    q_pckt = MsgQueuePacket(MsgType.CC_ADD_STREAM_REQ, "Hallo I bims ein Task")
    queue_register["cnc_connector"].send_msg(q_pckt, sender_name="cuc_application")
    queue_register["cnc_connector"].send_msg(q_pckt, sender_name="cuc_application")
    q_pckt = MsgQueuePacket(MsgType.CC_ADD_STREAM_REQ, "Hallo I bims zwei Task")
    queue_register["cnc_connector"].send_msg(q_pckt, sender_name="cuc_application")

    while True:
        logger.info("Waiting for input ... ")
        app_msg_queue.get_msg(blocking=True)
        logger.info("Message received, terminating cuc task ... ")
        break

    terminate_event.set()


# todo move to Task class
def init_task(task_name: str, queue_register: dict):
    """
    Instantiate a Task Object and add its queue to a task register
    @param task_name: Name of the task
    @param queue_register: Dict of all task queues by task name
    @return: Return the task
    """
    task = Task(name=task_name)
    queue_register[task.name] = task.msg_queue
    return task


if __name__ == '__main__':
    main()
    print("Exiting main", flush=True)

'''
TODOS here:
 - initiate the CUC tasks and message queues
    - lrp_dummy has special socket based message queue
    - rap_cuc_task has normal queue 
'''



