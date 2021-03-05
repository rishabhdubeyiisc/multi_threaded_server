#!/usr/bin/env python3
import socket 
import debugger_class
from time import time
import struct
import ctypes

verbose_control_FILE = True
use_debugger_FILE = True

class UDP_server:    
    def __init__(self , 
                 IP_addr = "127.0.0.1", 
                 port = 12345 , 
                 use_debugger = use_debugger_FILE , 
                 verbose_control = verbose_control_FILE , 
                 get_IPv4_override = False) :
        self.debugger_nw = debugger_class.debugger_class(create_dir=False ,
                                                         use_debugger=use_debugger_FILE, 
                                                         verbose_control = verbose_control_FILE,
                                                         filename = "UDP_server.log")
        self.debugger_nw.log("UDP_server_init","initializing UDP server")
        if (get_IPv4_override):
            self.IPAddr = self.get_my_ipv4()
        else :
            self.IPAddr = IP_addr
        self.port = port
        self.BUFFER_SIZE = 1024
        self.debugger_nw.log("UDP_server_init IPv4 ", self.IPAddr)
        self.debugger_nw.log("UDP_server_init PORT ", str(self.port))
        self.sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.debugger_nw.log("UDP_server_init SOCK ", str(self.sock))
        self.sender_addr = "127.0.0.1"
        try :
            self.debugger_nw.log("UDP_server_init ","sock.bind try")
            self.sock.bind((self.IPAddr,self.port))
        except socket.error as err :
            print("UDP server not binded")
            exit(-1)

    def get_my_ipv4(self):
        IP = '127.0.0.1'
        ip_resolver = socket.socket(socket.AF_INET , socket.SOCK_DGRAM)
        try :
            ip_resolver.connect(( '1.2.3.4' , 1 ))
            IP = ip_resolver.getsockname()[0]
        except Exception :
            IP = '127.0.0.1'
        finally :
            ip_resolver.close()
        return IP

    def recv_data(self):
        self.debugger_nw.log("UDP_server.recv_data","recieving data")
        data_recvd , self.sender_addr = self.sock.recvfrom(self.BUFFER_SIZE)        
        data_recvd = data_recvd.decode("utf-8")
        self.debugger_nw.log("UDP_server.recv_data","recieved data : " + str(data_recvd) + " from : " + str(self.sender_addr[0]))
        return str(data_recvd)
    
    def send_ack (self , string):
        self.debugger_nw.log("UDP_server.send_ack","sending data : " + str(string))
        message=bytes((string).encode("utf-8"))
        self.sock.sendto(message,self.sender_addr)
        self.debugger_nw.log( "UDP_server.send_ack"," sent data to : " + str(self.sender_addr[0]) )

    def send_msg (self , string , addr_to_send):
        pass

    def time_diff_calc(self):
        server_current_time = time()  # Get current timestamp
        server_SOC      = int(current_time_server)
        server_FRACSEC  = int( (((repr(( server_current_time % 1))).split("."))[1])[0:7] )

        client_SOC      = struct.unpack('!HHHIIH', data_recvd)[3]
        client_FRACSEC  = struct.unpack('!HHHIIH', data_recvd)[4]

        diff_SOC        = SOC_server - SOC_client
        diff_FRACSEC    = FRACSEC_server - FRACSEC_client 
        
        time_diff = ctypes.c_float ( ( SOC_diff + (FRACSEC_diff / 10000000) ) * 10000000 )  
        self.debugger_nw.log("UDP_server.time_diff_calc", "time_diff : " + str(time_diff))

        return time_diff
