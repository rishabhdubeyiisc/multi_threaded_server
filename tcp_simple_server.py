#! /usr/bin/env python3
import socket
import random
server_sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)

IP_SERVER_IS_BINDING = '127.0.0.1'
PORT_OPENING = 12345
BUFFER_SIZE = 1024
CONNECTION_TO_WAIT_WHILE_BUSY = 5
TRIALS_TO_DO = 10

def binding_mechanics(server_sock , base_port = 12345 , ip = '127.0.0.1' , trial_count_max = TRIALS_TO_DO ):
    trial = 0
    port = base_port 
    while ( trial <= trial_count_max ):
        try:
            server_sock.bind((ip,port))
            break
        except socket.error as bind_Err:
            trial = trial + 1
            port = port + 1
            print(str(bind_Err))
    return port

PORT_OPENING = binding_mechanics(server_sock=server_sock , base_port= PORT_OPENING , ip = IP_SERVER_IS_BINDING , trial_count_max = TRIALS_TO_DO )

server_sock.listen(CONNECTION_TO_WAIT_WHILE_BUSY)

while True:
    try :
        print("Server waiting for connection on port : " + str(PORT_OPENING) )
        client_socket_object , client_addr_tuple = server_sock.accept()
        print("Client connected from" , client_addr_tuple )
        # loop for reading the whole data as max size of buffer is 1024
        while True:
            data_recvd = client_socket_object.recv(BUFFER_SIZE)
            if not data_recvd or data_recvd.decode('utf-8') == 'END':
                break
            print("received from client : " + str(data_recvd.decode('utf-8')) )
            try :
                message_to_send = "hey client"
                client_socket_object.send(bytes(message_to_send.encode('utf-8')))
            except KeyboardInterrupt :
                print("\nexited by user")
        client_socket_object.close()
    except KeyboardInterrupt :
        print("\nexited by user")
        break
        
server_sock.close()