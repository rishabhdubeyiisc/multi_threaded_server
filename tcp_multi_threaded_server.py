#! /usr/bin/env python3
import socket
from _thread import *

server_sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)

IP_SERVER_IS_BINDING = '10.64.37.35'
PORT_OPENING = 12345
BUFFER_SIZE = 1024
thread_count = 0

try:
    server_sock.bind((IP_SERVER_IS_BINDING,PORT_OPENING))
except socket.error as bind_Err:
    print(str(bind_Err))

print("waiting for connection on")
server_sock.listen(5)

def client_thread(connection):
    message_to_send = "TCP multi thread here"
    connection.send(message_to_send.encode('utf-8'))
    while True:
        data_recvd = connection.recv(BUFFER_SIZE)
        reply = "Hello multi here" + str( data_recvd.decode('utf-8') )
        if not data_recvd : 
            break
        print(data_recvd.decode('utf-8'))
        connection.sendall( bytes(reply.encode('utf-8')) )
    connection.close()

while True:
    client_obj , client_addr_tuple = server_sock.accept()
    print("connected to : " + str(client_addr_tuple) )

    start_new_thread(client_thread , (client_obj,) )
    thread_count += 1
    print("Thread Number : " , thread_count)
    