#! /usr/bin/env python3
import socket
import datetime
import pytz
from time import time
from time import sleep as time_sleep
import array
import socket
import struct
import ctypes
from util import time_sync
import threading
#reolution is 0.1microsecond
SYNC_SPEED = 0.01 # in seconds
OFFSET = time_sync()

server_sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

IP_SERVER_IS_BINDING = '10.64.37.35'
PORT_OPENING = 12346
BUFFER_SIZE = 1024
try:
    server_sock.bind((IP_SERVER_IS_BINDING,PORT_OPENING))
except :
    print("bind error")

def sync_deamon(SYNC_SPEED):
    global OFFSET 
    while(True):
        OFFSET = time_sync()
        time_sleep(SYNC_SPEED)

def print_deamon(SYNC_SPEED):
    global OFFSET
    while True :
        print("value you want to observer : " + str(OFFSET) )
        time_sleep(SYNC_SPEED)

sync_deamon_TH = threading.Thread(target=sync_deamon , args=(SYNC_SPEED,))
sync_deamon_TH.setDaemon(True)
sync_deamon_TH.start()

printer = threading.Thread(target=print_deamon , args=(SYNC_SPEED,))
#printer.setDaemon(True)
#printer.start()

sqn_num = int(0) 
while True:
    # buffersize
    data_recvd , addr_of_client = server_sock.recvfrom(BUFFER_SIZE)
    
    current_time_server = time() + OFFSET  # Get current timestamp
    
    SOC_server = int(current_time_server)
    SOC_client = struct.unpack('!HHHIIH', data_recvd)[3]
    
    FRACSEC_server = ( int( (((repr(( current_time_server % 1))).split("."))[1])) ) 
    FRACSEC_client = struct.unpack('!HHHIIH', data_recvd)[4]
    
    SOC_diff        = SOC_server - SOC_client
    FRACSEC_diff    = FRACSEC_server - FRACSEC_client 
    #print ( str(addr_of_client) , struct.unpack('!HHHIIH', data_recvd) )
    net_Diff = ( SOC_diff * (10**7) ) + FRACSEC_diff 
    print(net_Diff)
    sqn_num = sqn_num + 1
    message_to_send = ( str(sqn_num) ).encode('utf-8')
    server_sock.sendto(message_to_send,addr_of_client)
