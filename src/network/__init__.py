import socket

def get_local_ip():
    ip = socket.gethostbyname(socket.gethostname())
    return ip
