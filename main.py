from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.utils import platform
import socket
import threading

import ssl
ssl._create_default_https_context = ssl._create_unverified_context

if platform == 'android':
    from android.permissions import request_permissions, Permission

    def request_android_permissions():
        request_permissions([
            Permission.INTERNET
        ])

HEADER = 64
PORT = 5050
FORMAT = "utf-8"
DISCONNECT_MESSAGE = "!DISCONNECT"
SERVER = "192.168.137.149"  # Vérifie bien que cette IP est correcte
ADDR = (SERVER, PORT)

class ClientApp(App):
    def build(self):
        if platform == 'android':
            request_android_permissions()
            #self.text = Label(request_android_permissions)
        
        layout = GridLayout(cols=1)
        self.label = Label(text="Enter a message:")
        self.input = TextInput()
        self.button = Button(text="Send")
        self.button.bind(on_press=self.send_message)
        
        layout.add_widget(self.label)
        layout.add_widget(self.input)
        layout.add_widget(self.button)
        return layout
    
    def connect_to_server(self):
        try:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.connect(ADDR)
            print("[CONNECTED] Successfully connected to the server")
        except Exception as e:
            print(f"[ERROR] Could not connect to server: {e}")
            self.client = None

    def send(self, msg):
        if self.client:
            try:
                message = msg.encode(FORMAT)
                msg_length = len(message)
                send_length = str(msg_length).encode(FORMAT)
                send_length += b" " * (HEADER - len(send_length))
                self.client.send(send_length)
                self.client.send(message)
                print(self.client.recv(2048).decode(FORMAT))
            except Exception as e:
                print(f"[ERROR] Failed to send message: {e}")

    def send_message(self, instance):
        self.send(self.input.text)

    def on_start(self):
        threading.Thread(target=self.connect_to_server, daemon=True).start()

ClientApp().run()