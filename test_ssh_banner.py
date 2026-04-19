import socket

s = socket.socket()
s.connect(("127.0.0.1", 2222))
banner = s.recv(1024)
print("RECEIVED BANNER:", banner)
s.close()
