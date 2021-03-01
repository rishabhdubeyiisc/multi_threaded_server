#! /usr/bin/env python3
import socket

client_sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

message_to_send = "Hello from client"

SERVER_IP = '10.64.37.35'
SERVER_PORT = 12345
BUFFER_SIZE = 1024

client_sock.sendto(message_to_send.encode('utf-8'),( SERVER_IP , SERVER_PORT) )

data_recvd , server_addr = client_sock.recvfrom(BUFFER_SIZE)

print ("Server says" + str (data_recvd.decode('utf-8')))

client_sock.close()
