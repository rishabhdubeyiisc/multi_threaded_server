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

#fr_seconds = int( (((repr((t % 1))).split("."))[1])[0:6])
def set_frasec( fr_seconds, leap_dir="+", leap_occ=False, leap_pen=False, time_quality=0):

    frasec = 1 << 1  # Bit 7: Reserved for future use. Not important but it will be 1 for easier byte forming.

    if leap_dir == "-":  # Bit 6: Leap second direction [+ = 0] and [- = 1].
        frasec |= 1

    frasec <<= 1

    if leap_occ:  # Bit 5: Leap Second Occurred, 1 in first second after leap second, remains 24h.
        frasec |= 1

    frasec <<= 1

    if leap_pen:  # Bit 4: Leap Second Pending - shall be 1 not more then 60s nor less than 1s before leap second.
        frasec |= 1

    frasec <<= 4  # Shift left 4 bits for message time quality

    # Bit 3 - 0: Message Time Quality indicator code - integer representation of bits (check table).
    frasec |= time_quality

    mask = 1 << 7  # Change MSB to 0 for standard compliance.
    frasec ^= mask

    frasec <<= 24  # Shift 24 bits for fractional time.

    frasec |= fr_seconds  # Bits 23-0: Fraction of second.

    return frasec


def int2frasec(frasec_int):

    tq = frasec_int >> 24
    leap_dir = tq & 0b01000000
    leap_occ = tq & 0b00100000
    leap_pen = tq & 0b00010000

    time_quality = tq & 0b00001111

    # Reassign values to create Command frame
    leap_dir = "-" if leap_dir else "+"
    leap_occ = bool(leap_occ)
    leap_pen = bool(leap_pen)

    fr_seconds = frasec_int & (2**23-1)

    return fr_seconds, leap_dir, leap_occ, leap_pen, time_quality

def get_frasec(frasec : int ):
    return int2frasec(frasec)[0]