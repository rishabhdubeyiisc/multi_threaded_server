#! /usr/bin/env python3

import socket

client_sock = socket.socket()

IP_SERVER_IS_BINDING = '127.0.0.1'
PORT_OPENING = 12345
BUFFER_SIZE = 1024

print("waiting for connection")
try:
    client_sock.connect((IP_SERVER_IS_BINDING,PORT_OPENING))
except socket.error as err :
    print( str(err) )

response = client_sock.recv(BUFFER_SIZE)
print(str ( response.decode('utf-8') ) )
while True:
    INPUT = input("say something")
    client_sock.send( INPUT.encode('utf-8') )
    response=client_sock.recv(BUFFER_SIZE)
    print(response.decode('utf-8'))
client_sock.close()