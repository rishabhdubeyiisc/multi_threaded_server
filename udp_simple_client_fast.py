#! /usr/bin/env python3
import threading
import socket
import datetime
import pytz
from time import time
import struct
from udp_payloads import common_frame_build

from util import time_sync
from util import sync_deamon
#reolution is 0.1microsecond
OFFSET = time_sync()

#from udp_packet_crafter import Common_frame

SERVER_IP = '127.0.0.1'
SERVER_PORT = 12346
BUFFER_SIZE = 1024

time_stamp = datetime.datetime.now(pytz.utc)

#protocol specific values
DATA_FRAME_VALUE    = int(0xAA01)
MAX_FRAME_SIZE      = int(0xFFFF)
IDCODE_VALUE        = int(0x0002)
SOC_VALUE           = int(0x99887766)

def sync_deamon():
    global OFFSET 
    while(True):
        OFFSET = time_sync()
        time_sleep(1)

def print_deamon():
    global OFFSET
    while True :
        print("value you want to observer : " + str(OFFSET) )
        time_sleep(2)

sync_deamon_TH = threading.Thread(target=sync_deamon)
#sync_deamon_TH.setDaemon(True)
sync_deamon_TH.start()

printer = threading.Thread(target=print_Func)
#printer.setDaemon(True)
#printer.start()

client_sock = socket.socket( family = socket.AF_INET, type= socket.SOCK_DGRAM )
sqn_num_sent = 0 
while True:
    #take input
    #payload = input("insert new payload > ")
    current_time = time() + OFFSET # Get current timestamp
    
    SOC_VALUE = int(current_time)
    #FRACSEC_VALUE = int( (((repr(( current_time % 1))).split("."))[1])[0:7] )
    FRACSEC_VALUE = ( int( (((repr(( current_time % 1))).split("."))[1])[0:7] ) )
    payload = common_frame_build (DATA_FRAME_VALUE , MAX_FRAME_SIZE , (0xDEAD) , SOC_VALUE , FRACSEC_VALUE , CHK= int(0xDEAD) )
    
    #send
    client_sock.sendto( payload ,( SERVER_IP , SERVER_PORT) )
    #recieve
    data_recvd , server_addr = client_sock.recvfrom(BUFFER_SIZE)
    sqn_num_sent = sqn_num_sent + 1 

    print ("Server says " + str (data_recvd.decode('utf-8')))

client_sock.close()
