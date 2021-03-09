import array
import socket
import struct
import ctypes
'''
SYNC        = 2 Bytes H
FRAME_SIZE  = 2 Bytes H
IDCODE      = 2 Bytes H
SOC         = 4 Bytes I
FRACSEC     = 4 Bytes I
DATA1       = 2 Bytes H
DATA2       = 2 Bytes H
CHK         = 2 Bytes H
'''
class Common_frame:
    def __init__(self,
                 SYNC       :  int,
                 FRAME_SIZE :  int,
                 IDCODE     :  int,
                 SOC        :  int,
                 FRACSEC    :  int, 
                 CHK        :  int                  
                 ):


        self.SYNC       = SYNC
        self.FRAME_SIZE = FRAME_SIZE
        self.IDCODE     = IDCODE
        self.SOC        = SOC
        self.FRACSEC    = FRACSEC
        self.CHK        = CHK

    def build(self) -> bytes:
        packet = struct.pack(
            '!HHHIIH',
            self.SYNC,    
            self.FRAME_SIZE,  
            self.IDCODE ,
            self.SOC ,
            self.FRACSEC  ,
            self.CHK  
        )
        return packet

class data_frame(Common_frame):
    pass
