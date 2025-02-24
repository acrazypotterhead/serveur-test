import socket
import threading
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock
from kivy.lang import Builder
from kivy_garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg
import matplotlib.pyplot as plt


HEADER = 64
PORT = 5050
SERVER = "192.168.5.27"  # Vérifie bien cette adresse IP
ADDR = (SERVER, PORT)
FORMAT = "utf-8"
DISCONNECT_MESSAGE = "!DISCONNECT"

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)

x_axis = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
x , y , z = [], [], []
plt.ion
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(5, 10))

class FirstWindow(Screen):
    def update_status(self, status):
        Clock.schedule_once(lambda dt: self.ids.status_label.setter('text')(self.ids.status_label, status))

    def update_messages(self, message):
        Clock.schedule_once(lambda dt: self.ids.messages.setter('text')(self.ids.messages, self.ids.messages.text + message + "\n"))

    def handle_client(self, conn, addr):
        self.update_status(f"[NEW CONNECTION] {addr} connected.")
        connected = True
        while connected:
            try:
                msg_length = conn.recv(HEADER).decode(FORMAT)
                if msg_length:
                    msg_length = int(msg_length)
                    msg = conn.recv(msg_length).decode(FORMAT)
                    if msg == DISCONNECT_MESSAGE:
                        connected = False
                        self.update_status(f"Device {addr} disconnected.")
                    self.update_messages(f"[{addr}] {msg}")
                    conn.send("Message received".encode(FORMAT))
            except:
                connected = False
        conn.close()

    def start_server(self):
        server.listen()
        self.update_status(f"[LISTENING] Server is listening on {SERVER}")
        while True:
            try:
                conn, addr = server.accept()
                thread = threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True)
                thread.start()
                self.update_status(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")
            except:
                break

    def stop_server(self):
        server.close()
        self.update_status("[STOPPED] Server has stopped.")

    def on_enter(self):
        threading.Thread(target=self.start_server, daemon=True).start()


class SecondWindow(Screen):
    pass


class WindowManager(ScreenManager):
    pass


class ServerApp(App):
    def build(self):
        return Builder.load_file("interface_serveur.kv")


if __name__ == "__main__":
    ServerApp().run()
