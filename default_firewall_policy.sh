#!/bin/sh

# Flushing all rules
iptables -F
iptables -X
# Setting default filter policy
iptables -P INPUT ACCEPT
iptables -P OUTPUT ACCEPT
iptables -P FORWARD ACCEPT