#! /usr/bin/env python3
import socket
import datetime
import pytz
from time import time

from udp_packet_crafter import Common_frame

SERVER_IP = '10.64.37.35'
SERVER_PORT = 12345
BUFFER_SIZE = 1024

time_stamp = datetime.datetime.now(pytz.utc)

#protocol specific values
DATA_FRAME_VALUE = 0xAA01
MAX_FRAME_SIZE = 0xFFFF
IDCODE_VALUE = 0x0002
SOC_VALUE = 0x99
client_sock = socket.socket( family = socket.AF_INET, type= socket.SOCK_DGRAM )

while True:
    #take input
    #payload = input("insert new payload > ")
    current_time = datetime.datetime.now(pytz.utc)  # Get current timestamp

    crafted_payload = Common_frame( SYNC        = int(DATA_FRAME_VALUE) , 
                                    FRAME_SIZE  = int(MAX_FRAME_SIZE), 
                                    IDCODE      = int(0xDEAD) , 
                                    SOC         = int(current_time) , 
                                    FRACSEC     = int( (((repr(( current_time % 1))).split("."))[1])[0:7] ) , 
                                    CHK         = int(0xDEAD) )
    
    payload = crafted_payload.build()
    #send
    client_sock.sendto( payload ,( SERVER_IP , SERVER_PORT) )
    #recieve
    data_recvd , server_addr = client_sock.recvfrom(BUFFER_SIZE)
    print ("Server says" + str (data_recvd.decode('utf-8')))

client_sock.close()
