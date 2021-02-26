#! /usr/bin/env python3
import socket
import threading

server_sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

IP_SERVER_IS_BINDING = '127.0.0.1'
PORT_OPENING = 12345
BUFFER_SIZE = 1024
thread_count = 0

try:
    server_sock.bind((IP_SERVER_IS_BINDING,PORT_OPENING))
except socket.error as bind_Err:
    print(str(bind_Err))

#server_sock.listen(100) THIS IS DONE IN TCP
def client_thread(connection):
    message_to_send = "UDP multi thread here"
    connection.send(message_to_send.encode('utf-8'))
    while True:
        data_recvd , addr_of_client = connection.recvfrom(BUFFER_SIZE)
        if not data_recvd: 
            break
        print(data_recvd.decode('utf-8'))
        message_to_send = ("UDP server here").encode('utf-8')
        connection.sendto(message_to_send,addr_of_client)
    connection.close()

while True:
    #client , address = server_sock.accept()
    