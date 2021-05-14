import enum

class MsgType(enum.IntEnum):
    """ Message Types the messages interchanged by the tasks via a message queue
         All messages names follow the same structure: Prefix_Name_Suffix
        Prefix = Task responsible for the message
        Name = Indicates what the message transports/is used for
        Suffix =
            - REQest = The task indicated in "prefix" offers a service/resource to an other task
            - INDitcation = The task mentioned in "prefix" indicates an event/result to an other task
    """
    LRP_ASSOCIATE_PORTAL_REQ = 0x1000,
    LRP_RECORD_WRITTEN_IND= 0x1001,
    LRP_DELETE_RECORD_REQ = 0x1002,
    LRP_LOCAL_TARGET_PORT_REQ = 0x1003,
    LRP_NEIGHBOUR_TARGET_PORT_REQ = 0x1004,
    LRP_FIRST_HELLO_IND = 0x1005,
    LRP_PORTAL_STATUS_IND = 0x1006,
    RPSI_DECLARE_REQ = 0x2000,
    RPSI_WITHDRAW_REQ = 0x2001,
    RPSI_REGISTER_IND = 0x2002,
    RPSI_DEREGISTER_IND = 0x2003,
    PC_REG_TALKER_REQUIREMENT_IND = 0x3000,
    PC_REG_LISTENER_REQUIREMENT_IND = 0x3001,
    PC_DEREG_TALKER_REQUIREMENT_IND = 0x3002,
    PC_DEREG_LISTENER_REQUIREMENT_IND = 0x3003,
    SM_STREAM_STATUS_IND = 0x4000,
    CC_ADD_STREAM_REQ = 0x5000,
    CC_UPDATE_STREAM_REQ = 0x5001,
    CC_REMOVE_STREAM_REQ = 0x5002,
    CC_ADD_LISTENER_REQ = 0x5003,
    CC_REM_LISTENER_REQ = 0x5004,
    CC_UPDATE_LISTENER_REQ = 0x5005,
    CC_RESERVATION_RESULT_IND = 0x5006,
    WHH_GET_HOOK_ADDR_REQ = 0x6000,
    WHH_GET_HOOK_ADDR_IND = 0x6001,
    WHH_RESULT_IND = 0x6002
