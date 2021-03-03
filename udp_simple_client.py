#! /usr/bin/env python3
import socket
from udp_packet_crafter import Common_frame

SERVER_IP = '10.64.37.35'
SERVER_PORT = 12345
BUFFER_SIZE = 1024

client_sock = socket.socket( family = socket.AF_INET, type= socket.SOCK_DGRAM )
crafted_payload = Common_frame(SYNC = 256 , FRAME_SIZE = 100 , IDCODE = 4 , SOC = 10000 , FRACSEC= 12000 , CHK = 103 )
payload = crafted_payload.build()
while True:
    #take input
    #payload = input("insert new payload > ")
    #send
    client_sock.sendto( payload.encode('utf-8'),( SERVER_IP , SERVER_PORT) )
    #recieve
    data_recvd , server_addr = client_sock.recvfrom(BUFFER_SIZE)
    print ("Server says" + str (data_recvd.decode('utf-8')))

client_sock.close()
