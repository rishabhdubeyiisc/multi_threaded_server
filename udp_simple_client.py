#! /usr/bin/env python3
import socket


SERVER_IP = '10.64.37.35'
SERVER_PORT = 12345
BUFFER_SIZE = 1024

client_sock = socket.socket( family = socket.AF_INET, type= socket.SOCK_DGRAM )

while True:
    #take input
    new_payload = input("insert new payload > ")
    #send
    client_sock.sendto( payload.encode('utf-8'),( SERVER_IP , SERVER_PORT) )
    #recieve
    data_recvd , server_addr = client_sock.recvfrom(BUFFER_SIZE)
    print ("Server says" + str (data_recvd.decode('utf-8')))

client_sock.close()
