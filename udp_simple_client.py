#! /usr/bin/env python3
import socket
import datetime 
from udp_packet_crafter import Common_frame

SERVER_IP = '127.0.0.1'
SERVER_PORT = 12345
BUFFER_SIZE = 1024

time_stamp = datetime.datetime.now(pytz.utc)

#protocol specific values
DATA_FRAME_VALUE = 0xAA01
MAX_FRAME_SIZE = 0xFFFF
IDCODE_VALUE = 0x0002
SOC_VALUE = 
client_sock = socket.socket( family = socket.AF_INET, type= socket.SOCK_DGRAM )
crafted_payload = Common_frame(SYNC = int(DATA_FRAME_VALUE) , FRAME_SIZE = int(MAX_FRAME_SIZE), IDCODE = int(0xDEAD) , SOC = int(0xABCDEF12) , FRACSEC= int(0x12345678) , CHK = int(0xEABD) )
payload = crafted_payload.build()
while True:
    #take input
    #payload = input("insert new payload > ")
    #send
    client_sock.sendto( payload ,( SERVER_IP , SERVER_PORT) )
    #recieve
    data_recvd , server_addr = client_sock.recvfrom(BUFFER_SIZE)
    print ("Server says" + str (data_recvd.decode('utf-8')))

client_sock.close()
