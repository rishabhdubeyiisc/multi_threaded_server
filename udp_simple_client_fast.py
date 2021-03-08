#! /usr/bin/env python3
import socket
import datetime
import pytz
from time import time
import struct
from udp_payloads import common_frame_build

#from udp_packet_crafter import Common_frame

SERVER_IP = '10.64.37.35'
SERVER_PORT = 12345
BUFFER_SIZE = 1024

time_stamp = datetime.datetime.now(pytz.utc)

#protocol specific values
DATA_FRAME_VALUE    = int(0xAA01)
MAX_FRAME_SIZE      = int(0xFFFF)
IDCODE_VALUE        = int(0x0002)
SOC_VALUE           = int(0x99887766)

client_sock = socket.socket( family = socket.AF_INET, type= socket.SOCK_DGRAM )

while True:
    #take input
    #payload = input("insert new payload > ")
    current_time = time()  # Get current timestamp
    
    SOC_VALUE = int(current_time)
    #FRACSEC_VALUE = int( (((repr(( current_time % 1))).split("."))[1])[0:7] )
    FRACSEC_VALUE = int( (((repr(( current_time % 1))).split("."))[1])[0:7] ) 
    payload = common_frame_build (DATA_FRAME_VALUE , MAX_FRAME_SIZE , (0xDEAD) , SOC_VALUE , FRACSEC_VALUE , CHK= int(0xDEAD) )
    
    #send
    client_sock.sendto( payload ,( SERVER_IP , SERVER_PORT) )
    #recieve
    data_recvd , server_addr = client_sock.recvfrom(BUFFER_SIZE)
    print ("Server says" + str (data_recvd.decode('utf-8')))

client_sock.close()
