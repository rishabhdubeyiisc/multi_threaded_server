#! /usr/bin/env python3
import socket
import datetime
import pytz
from time import time
import array
import socket
import struct
import ctypes
#reolution is 0.1microsecond
server_sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

IP_SERVER_IS_BINDING = '10.64.37.35'
PORT_OPENING = 12345
BUFFER_SIZE = 1024
try:
    server_sock.bind((IP_SERVER_IS_BINDING,PORT_OPENING))
except :
    print("bind error")

sqn_num = 0 
while True:
    # buffersize
    data_recvd , addr_of_client = server_sock.recvfrom(BUFFER_SIZE)
    
    current_time_server = time()  # Get current timestamp
    
    SOC_server = int(current_time_server)
    SOC_client = struct.unpack('!HHHIIH', data_recvd)[3]
    
    FRACSEC_server = int( (((repr(( current_time % 1))).split("."))[1])[0:7] )
    FRACSEC_client = struct.unpack('!HHHIIH', data_recvd)[4]
    
    SOC_diff        = SOC_server - SOC_client
    FRACSEC_diff    = FRACSEC_server - FRACSEC_client 
    #print ( str(addr_of_client) , struct.unpack('!HHHIIH', data_recvd) )
    net_Diff = ( SOC_diff * (10**7) ) + FRACSEC_diff 
    print(net_Diff)
    sqn_num = sqn_num + 1
    message_to_send = ("UDP server here").encode('utf-8')
    server_sock.sendto(message_to_send,addr_of_client)