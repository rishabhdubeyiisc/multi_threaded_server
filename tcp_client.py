#! /usr/bin/env python3
import socket

client_sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)

message_to_send = "Hello from client"

SERVER_IP = '10.64.37.30'
SERVER_PORT = 12345
BUFFER_SIZE = 1024
TRIALS_TO_DO = 10 

def connect_mechanics(ip = '127.0.0.1' , port = 12345 , trials_to_do = 10 ):
    trials = 0
    while (trials <= trials_to_do ):
        try :
            client_sock.connect((ip,port))
            break
        except socket.error as err :
            print ( "connection refused for port : " + str(port) + "Error : " + str(err) )
            trials = trials  + 1
            port = port + 1
    return port

SERVER_PORT = connect_mechanics(ip=SERVER_IP , port = SERVER_PORT ,trials_to_do= TRIALS_TO_DO)
print("Connected to : ", str(SERVER_IP) , str(SERVER_PORT) )
payload = "Hey server"

try :
    while True:
        client_sock.send(payload.encode('utf-8'))
        data_recvd = client_sock.recvfrom(BUFFER_SIZE)
        print ("Server says : " + str (data_recvd[0].decode('utf-8') ))
        want_to_send_more = input("do you want to send more data Y/n ") 
        if (want_to_send_more.lower() == 'y') : 
            payload = input("Enter payload to send > ")
        else :
            break 
except KeyboardInterrupt :
    print("\nexited by user")
client_sock.close()
