#!/bin/sh
# My system IP/set ip address of server
SSH_SERVER_IP="10.64.37.34"
SSH_CLIENT_IP="10.64.37.35"

UDP_CLIENT1_IP="10.64.37.31"
UDP_CLIENT2_IP="10.64.37.32"
UDP_CLIENT3_IP="10.64.37.33"
UDP_CLIENT4_IP="10.64.37.34"
UDP_SERVER_IP="10.64.37.35"

# Flushing all rules
iptables -F
iptables -X
# Setting default filter policy
iptables -P INPUT DROP
iptables -P OUTPUT DROP
iptables -P FORWARD DROP
# Allow unlimited traffic on loopback
iptables -A INPUT -i lo -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT
 
# Allow incoming ssh over tcp
iptables -A INPUT -p tcp -s $SSH_CLIENT_IP -d $SSH_SERVER_IP --sport 513:65535 --dport 22 -m state --state NEW,ESTABLISHED -j ACCEPT
iptables -A OUTPUT -p tcp -s $SSH_SERVER_IP -d $SSH_CLIENT_IP --sport 22 --dport 513:65535 -m state --state ESTABLISHED -j ACCEPT
# Allow incoming udp connections for PMUs
iptables -A INPUT -p udp -s $UDP_CLIENT2_IP -d $SERVER_IP --sport 12300:12400 --dport 12300:12400 -j FORWARD
iptables -A OUTPUT -p udp -s $SERVER_IP -d $UDP_CLIENT2_IP --sport 12300:12400 --dport 12300:12400 -j FORWARD

iptables -A INPUT -p udp -s $UDP_CLIENT1_IP -d $SERVER_IP --sport 12300:12400 --dport 12300:12400 -j FORWARD
iptables -A OUTPUT -p udp -s $SERVER_IP -d $UDP_CLIENT1_IP --sport 12300:12400 --dport 12300:12400 -j FORWARD

iptables -A INPUT -p udp -s $UDP_CLIENT3_IP -d $SERVER_IP --sport 12300:12400 --dport 12300:12400 -j FORWARD
iptables -A OUTPUT -p udp -s $SERVER_IP -d $UDP_CLIENT3_IP --sport 12300:12400 --dport 12300:12400 -j FORWARD

iptables -A INPUT -p udp -s $UDP_CLIENT4_IP -d $SERVER_IP --sport 12300:12400 --dport 12300:12400 -j ACCEPT
iptables -A OUTPUT -p udp -s $SERVER_IP -d $UDP_CLIENT4_IP --sport 12300:12400 --dport 12300:12400 -j ACCEPT

# make sure nothing comes or goes out of this box
iptables -A INPUT -j DROP
iptables -A OUTPUT -j DROP