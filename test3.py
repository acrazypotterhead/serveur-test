from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty
from kivy.clock import mainthread

import socket

import threading
import time

HEADER = 64
PORT = 5050
SERVER = "192.168.5.27"  # Vérifie bien cette adresse IP
ADDR = (SERVER, PORT)
FORMAT = "utf-8"
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)
server.listen()

class MyBL(BoxLayout):
    counter = 0
    data_label = StringProperty("Nothing yet!")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        threading.Thread(target=self.get_data).start()

    def get_data(self):
        while App.get_running_app():
            # get data here
            # sock.recv(1024) or how you do it
            conn, addr = server.accept()
            threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True).start()
            time.sleep(1)

            # if you change the UI you need to do it on main thread
            self.set_data_label(self.counter)

            self.counter += 1

    @mainthread
    def set_data_label(self, data):
        self.data_label = str(data)

KV = """
MyBL:
    Label:
        font_size: "30sp"
        text: "Some Data"
    Label:
        font_size: "30sp"
        text: root.data_label
"""

class MyApp(App):
    def build(self):
        return Builder.load_string(KV)

MyApp().run()