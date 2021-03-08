import struct 
def common_frame_build(SYNC       : int , 
             FRAME_SIZE : int , 
             IDCODE     : int , 
             SOC        : int , 
             FRACSEC    : int , 
             CHK        : int ) -> bytes:
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