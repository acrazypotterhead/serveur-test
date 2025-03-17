import socket
import random
HEADER = 64
PORT = 5050
FORMAT = "utf-8"
serveur_ip = "192.168.5.27"

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((serveur_ip, PORT))


while True:
    msg = f"{random.randint(-40,40)}, {random.randint(-40,40)}, {random.randint(-40,40)}"
    message = msg.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b" " * (HEADER - len(send_length))
    client.sendall(send_length + message)