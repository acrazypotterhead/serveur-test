import socket
import threading
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock
from kivy.lang import Builder
import kivy_matplotlib_widget  # Import du widget optimisé
from matplotlib import pyplot as plt
from matplotlib.ticker import MaxNLocator
import numpy as np

# Configuration du serveur
HEADER = 64
PORT = 5050
SERVER = "192.168.5.27"
ADDR = (SERVER, PORT)
FORMAT = "utf-8"
DISCONNECT_MESSAGE = "!DISCONNECT"

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)

# Données pour le graphe
N = 10000
xdata = np.arange(N)
ydata, ydata2 = [], []

# Nombre max de points affichés
max_data_window = 1000
ratio_data = 2

# Création du graphique
fig, ax1 = plt.subplots()
line1, = plt.plot([], [], color="green", label="Low")
line2, = plt.plot([], [], color="red", label="High")
ax1.xaxis.set_major_locator(MaxNLocator(prune='lower', nbins=5))
ax1.set_xlim(0, max_data_window)
ax1.set_ylim(-10, 10)

class FirstWindow(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.min_index = 0
        self.max_index = 1
        self.current_xmax_refresh = max_data_window
        Clock.schedule_once(self.add_graph)

    def add_graph(self, dt):
        """Ajoute le graphe à l'interface Kivy."""
        self.ids.box_graph.figure = fig
        self.ids.box_graph.xmin = 0
        self.ids.box_graph.xmax = max_data_window
        Clock.schedule_interval(self.update_graph, 1 / 60)

    def update_status(self, status):
        Clock.schedule_once(lambda dt: setattr(self.ids.status_label, 'text', status))

    def update_messages(self, message):
        Clock.schedule_once(lambda dt: setattr(self.ids.messages, 'text', self.ids.messages.text + message + "\n"))

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
                        break

                    split_msg = msg.split(",")
                    if len(split_msg) == 2:
                        ydata.append(float(split_msg[0]))
                        ydata2.append(float(split_msg[1]))

                        if len(ydata) > N:
                            ydata.pop(0)
                            ydata2.pop(0)

                    self.update_messages(f"[{addr}] {msg}")
                    conn.send("Message received".encode(FORMAT))
            except:
                connected = False
        conn.close()

    def update_graph(self, *args):
        """Met à jour le graphe avec les nouvelles données."""
        if len(ydata) > 0:
            min_idx = max(0, len(ydata) - max_data_window)
            line1.set_data(xdata[min_idx:len(ydata)], ydata[min_idx:])
            line2.set_data(xdata[min_idx:len(ydata2)], ydata2[min_idx:])
            
            self.ids.box_graph.xmin = xdata[min_idx]
            self.ids.box_graph.xmax = xdata[len(ydata) - 1]
            self.ids.box_graph.home()
        
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
