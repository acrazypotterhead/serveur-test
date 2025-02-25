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


x_axis = list(range(21))
x , y , z = [], [], []

fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(5, 10))

class FirstWindow(Screen):
    def __init__(self, **kwargs):
        super(FirstWindow, self).__init__(**kwargs)
        Clock.schedule_once(self.add_graph)

    def add_graph(self, dt):
        self.ids.box_graph.add_widget(FigureCanvasKivyAgg(fig))

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

                    split_msg = msg.split(",")

                    if len(split_msg) ==3:
                        x.append(float(split_msg[0]))
                        y.append(float(split_msg[1]))
                        z.append(float(split_msg[2]))

                    if len(x) > 20:
                        x.pop(0)
                        y.pop(0)
                        z.pop(0)
                    
                    ax1.clear()
                    ax2.clear()
                    ax3.clear()

                    ax1.plot(x_axis[-len(x):], x, 'r-')
                    ax2.plot(x_axis[-len(y):], y, 'g-')
                    ax3.plot(x_axis[-len(z):], z, 'b-')

                    ax1.set_title("X Axis")
                    ax2.set_title("Y Axis")
                    ax3.set_title("Z Axis")

                    fig.canvas.draw()



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
