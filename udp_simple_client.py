#! /usr/bin/env python3
import socket


SERVER_IP = '10.64.37.35'
SERVER_PORT = 12345
BUFFER_SIZE = 1024

client_sock = socket.socket( family = socket.AF_INET, type= socket.SOCK_DGRAM )

payload = "Hello from client 1902388474 1.098377328329 1.0011 0x128900238 "

client_sock.sendto( payload.encode('utf-8'),( SERVER_IP , SERVER_PORT) )

data_recvd , server_addr = client_sock.recvfrom(BUFFER_SIZE)

print ("Server says" + str (data_recvd.decode('utf-8')))

client_sock.close()
