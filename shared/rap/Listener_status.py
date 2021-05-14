import enum
class Listener_status(enum.IntEnum):
    NONE = 0,
    READY = 1,
    PARTIAL_FAILED = 2,
    FAILED = 3,

