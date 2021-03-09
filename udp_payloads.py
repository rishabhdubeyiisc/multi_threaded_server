import struct 

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
MAX_16_BIT = 65535
MAX_32_BIT = 2**32 - 1
MAX_24_BIT = 2**24 - 1

def ERR_SYNC(val):
    print("ERR_SYNC : Value = " , val)

def ERR_FRAME_SIZE(val):
    print("ERR_FRAME_SIZE : Value = " , val)

def ERR_SOC(val):
    print("ERR_SOC : Value = " , val)

def ERR_FRACSEC(val):
    print("ERR_FRACSEC : Value = " , val)

def common_frame_build(SYNC       : int , 
             FRAME_SIZE : int , 
             IDCODE     : int , 
             SOC        : int , 
             FRACSEC    : int , 
             CHK        : int ) -> bytes:
    if not ( 0xAA00 <= SYNC         <= 0xAA6F ):
        ERR_SYNC(SYNC)
        exit(-1)
    if not ( 0      <= FRAME_SIZE   <= MAX_16_BIT ):
        ERR_FRAME_SIZE(FRAME_SIZE)
        exit(-1)
    if not ( 0      <= SOC   <= MAX_32_BIT ):
        ERR_SOC(SOC)
        exit(-1)
    if not ( 0      <= FRACSEC   <= MAX_24_BIT ):
        ERR_FRACSEC(FRACSEC)
        exit(-1)

    packet = struct.pack(
        '!HHHIIH',
        SYNC,    
        FRAME_SIZE,  
        IDCODE ,
        SOC ,
        FRACSEC  ,
        CHK  
    )
    return packet