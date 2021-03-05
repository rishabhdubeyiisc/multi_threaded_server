#!/usr/bin/env python3
import udp_server_class

if __name__ == "__main__":
    udp_server = udp_server_class.UDP_server(IP_addr='10.64.37.35',
                                            port = 12345 ,
                                            use_debugger= True,
                                            verbose_control= False,
                                            get_IPv4_override=False,
                                            create_dir=True)
    
    sqn_num = 0
    while True:
        #rcvd
        data_rcvd = udp_server.recv_bytes()
        #time
        time_diff_tuple = udp_server.time_diff_calc(data_rcvd)
        print(str(time_diff_tuple))
        #send
        #udp_server.send_ack(str(sqn_num))
        #sqn_num = sqn_num + 1