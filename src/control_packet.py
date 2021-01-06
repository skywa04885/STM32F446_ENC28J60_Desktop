import enum
from struct import unpack

CONTROL_PORT = 7588

CONTROL_PACKET_FLAG_ERR = 0
CONTROL_PACKET_FLAG_OK = 1

CONTROL_PREFIX = b'pointytits'

class ControlPacketMotorMode(enum.Enum):
    Auto = 0
    Manual = 1

class ControlPacketMotorType(enum.Enum):
    Stepper = 0
    Servo = 1
    DC = 2

class ControlPacketType(enum.Enum):
    Request = 0
    Reply = 1

class ControlPacketOpcode(enum.Enum):
    MotorInfo = 0
    StepperMove = 1
    StepperEnable = 2
    StepperDisable = 3
    StepperStats = 4

class ControlPacketArgType(enum.Enum):
    Padd = 0
    Motor = 1
    String = 2
    U8 = 3
    U16 = 4
    U32 = 5
    U64 = 6
    I8 = 7
    I16 = 8
    I32 = 9
    I64 = 10
    MotorStatus = 11
    End = 0xFFFF

class ControlPacketArgStepperStatus:
    def __init__ (self, id_, flags, sps, cpos, tpos):
        self.id_ = id_
        self.flags = flags
        self.sps = sps
        self.cpos = cpos
        self.tpos = tpos

    def parse(buffer):
        id_, f, sps, cpos, tpos = unpack('<BBHii', buffer)
        return ControlPacketArgStepperStatus(id_, f, sps, cpos, tpos)

