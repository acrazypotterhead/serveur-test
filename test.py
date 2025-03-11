import socket
import threading
import time

HEADER = 64
PORT = 5050
SERVER = "192.168.5.27"  # Vérifiez bien cette adresse IP
ADDR = (SERVER, PORT)
FORMAT = "utf-8"
DISCONNECT_MESSAGE = "!DISCONNECT"

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)
x = []
y = []
z = []
data_count = 0

def update_status(status):
    print(status)

def update_messages(message):
    print(message)

def handle_client(conn, addr):
    global data_count
    update_status(f"[NEW CONNECTION] {addr} connected.")
    connected = True
    
    while connected:
        try:
            raw_msg_length = conn.recv(HEADER).decode(FORMAT)
            # On retire les espaces blancs
            msg_length_str = raw_msg_length.strip()

            if msg_length_str:
                msg_length = int(msg_length_str)
                msg = conn.recv(msg_length).decode(FORMAT)

                #print(f"Received message: {msg}")
                split_msg = msg.split(",")
                if len(split_msg) == 3:
                    x.append(float(split_msg[0]))
                    y.append(float(split_msg[1]))
                    z.append(float(split_msg[2]))

                    data_count += 1 

            if msg == DISCONNECT_MESSAGE:
                connected = False
                #update_status(f"Device {addr} disconnected.")
            
            #update_messages(f"[{addr}] {msg}")
            
        except Exception as e:
            print(f"[ERROR] {e}")
            connected = False
    conn.close()



def start_server():
    server.listen()
    update_status(f"[LISTENING] Server is listening on {SERVER}")
    while True:
        try:
            conn, addr = server.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            thread.start()
            update_status(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")
        except Exception as e:
            print(f"[ERROR] {e}")
            break

def reset_data_count():
    global data_count
    while True:
        print(f"Data per second: {data_count}")
        data_count = 0
        time.sleep(1)

if __name__ == "__main__":
    threading.Thread(target=reset_data_count, daemon=True).start()
    start_server()


