from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
import socket

import time
from kivy.uix.textinput import TextInput

HEADER = 64
PORT = 5050
FORMAT = "utf-8"
DISCONNECT_MESSAGE = "!DISCONNECT"
SERVER = "192.168.56.1"
ADDR = (SERVER, PORT)

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(ADDR)

def send(msg):
    message = msg.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b" " * (HEADER - len(send_length))
    client.send(send_length)
    client.send(message)
    print(client.recv(2048).decode(FORMAT))
    
class ClientApp(App):
    def build(self):
        layout = GridLayout(cols=1)
        self.label = Label(text="Enter a message:")
        self.input = TextInput()
        self.button = Button(text="Send")
        self.button.bind(on_press=self.send_message)
        layout.add_widget(self.label)
        layout.add_widget(self.input)
        layout.add_widget(self.button)
        return layout
    
    def send_message(self, instance):
        send(self.input.text)


#send("Hello World!")
#send("Hello World!")
#send("Hello World!")
#send(DISCONNECT_MESSAGE)

ClientApp().run()