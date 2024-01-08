#!/bin/python3

import socket

def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("1.2.3.4", 80))
    return s.getsockname()[0]

ip = get_ip_address()
print(ip)