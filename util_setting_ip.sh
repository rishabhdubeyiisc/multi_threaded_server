#!/bin/bash
ifconfig enp0s31f6 10.64.37.35 netmask 255.255.255.0 up

route add default gw 10.64.37.1

echo "nameserver 1.1.1.1" > /etc/resolv.conf