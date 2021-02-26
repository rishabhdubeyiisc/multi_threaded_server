#! /usr/bin/env python3
import socket

server_sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

IP_SERVER_IS_BINDING = '127.0.0.1'
PORT_OPENING = 12345
BUFFER_SIZE = 1024
try:
    server_sock.bind((IP_SERVER_IS_BINDING,PORT_OPENING))
except :
    print("bind error")
while True:
    # buffersize
    data_recvd , addr_of_client = server_sock.recvfrom(BUFFER_SIZE)
    print (data_recvd.decode('utf-8'))
    message_to_send = ("UDP server here").encode('utf-8')
    server_sock.sendto(message_to_send,addr_of_client)