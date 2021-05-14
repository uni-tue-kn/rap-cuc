import enum


"""
There are currently no failure codes defined for RAP, so we took some of the old MSRP Reservation from 802.1Q 35-6 Table
"""
class Failure_code(enum.IntEnum):
    ERROR = 0,
    INSUFFICIENT_BANDWIDTH = 1,  # in use
    INSUFFICIENT_BRIGE_RES = 2,
    INSUFFICIENT_BANDWIDTH_FOR_TC = 3,
    STREAM_ID_IN_USE = 4,
    STREAM_DST_IN_USE = 5,
    STREAM_PREMPTED_BY_RANK = 6,
    PRIO_NOT_AN_RA_CLASS = 13,  # in use
    RA_CLASS_PRIO_MISMATCH = 19, # in use
    MAC_LATENCY_EXCEEDED = 21,

