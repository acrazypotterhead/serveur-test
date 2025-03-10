from kivy.uix.recyclegridlayout import defaultdict
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.utils import platform
import socket
import threading
import time
from plyer import accelerometer
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.lang import Builder
from widgets import Jauge 
from kivy.core.window import Window

import ssl
ssl._create_default_https_context = ssl._create_unverified_context

if platform == 'android':
    from android.permissions import request_permissions, Permission

    def request_android_permissions():
        request_permissions([
            Permission.INTERNET
        ])

Window.size = (340, 620)
Window.clearcolor = (46/255, 46/255, 46/255)
Builder.load_file('jauge.kv')



HEADER = 64
PORT = 5050
FORMAT = "utf-8"
DISCONNECT_MESSAGE = "!DISCONNECT"
#SERVER = "192.168.137.248"  # Vérifie bien que cette IP est correcte
#ADDR = (SERVER, PORT)
serveur_ip = ""




class FirstWindow(Screen):

    def __init__(self, **kwargs):
        super(FirstWindow, self).__init__(**kwargs)
        self.data_count = 0  # Compteur de données
        self.sensor = False

    
    def start_gyroscope(self, instance):
        threading.Thread(target=self.collect_accelerometer_data).start()

    


    def set_server_ip(self):
        self.serveur_ip = self.ids.ip.text  # Store the server IP in an instance variable
        print(f"Server IP set to: {self.serveur_ip}")
        # Start the connection in a new thread to avoid blocking the UI
        self.connect_to_server(self.serveur_ip)


    
    def connect_to_server(self, serveur_ip):
        try:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.connect((serveur_ip, PORT))
            self.ids.label_ip.text = f"Connected to {serveur_ip}"
            
        except Exception as e:
            self.ids.label_ip.text = f"[ERROR] Could not connect to server: {e}"
            self.client = None
            

    def send(self, msg):
        if self.client:
            threading.Thread(target=self._send_thread, args=(msg,)).start()

    def _send_thread(self, msg):
        try:
            message = msg.encode(FORMAT)
            msg_length = len(message)
            send_length = str(msg_length).encode(FORMAT)
            send_length += b" " * (HEADER - len(send_length))
            self.client.send(send_length)
            self.client.send(message)
        except Exception as e:
            print(f"[ERROR] Failed to send message: {e}")
            
    def send_message(self):
        message = self.ids.message.text  # Get the message from the input
        self.send(message)



    def do_toggle(self, *_args):   
        if not self.sensor:
            try:
                accelerometer.enable()
                self.sensor = True
            except:
                print("Accelerometer is not implemented for your platform")
    
            if self.sensor:
                Clock.schedule_interval(self.collect_accelerometer_data, 1/90)
                

                Clock.schedule_interval(self.reset_data_count, 1)
            else:
                accelerometer.disable()
        else:
            # Stop de la capture
            accelerometer.disable()
            Clock.unschedule(self.get_acceleration)
            Clock.unschedule(self.reset_data_count)
    
            # Retour à l'état arrété
            self.sensor = False
            
        
    

    def collect_accelerometer_data(self, dt):
        
        try:
            val = accelerometer.acceleration[:3]
            if val is not None:
                self.data_count += 1
                val_x, val_y, val_z = val
                self.ids.button_gyro.text = f"x: {val_x:.2f}, y: {val_y:.2f}, z: {val_z:.2f}"
                self.send(f"{val_x:.0f},{val_y:.0f},{val_z:.0f}")  # Envoie les données au serveur
        except Exception as e:
            print(f"[ERROR] Impossible de lire l'accéléromètre : {e}")


    def reset_data_count(self, dt):
        print(f"Data per second: {self.data_count}")
        self.ids.data.text = f"Data per second: {self.data_count}"
        self.data_count = 0  # Réinitialiser le compteur
        
        #while True:
        #    try:
        #        if accelerometer.is_available():
        #            accelerometer.enable()
        #            time.sleep(1)  # Wait for the sensor to initialize
        #            data = accelerometer.acceleration[:3]
        #            if data:
        #                x, y, z = data
        #                accelerometer_data = f"Gyroscope data - x: {x}, y: {y}, z: {z}"
        #                print(accelerometer_data)
        #                self.send(accelerometer_data)
        #                
        #            accelerometer.disable()
        #        time.sleep(1)  # Collect data every second
        #    except Exception as e:
        #        print(f"[ERROR] Failed to collect gyroscope data: {e}")


class SecondWindow(Screen):
    pass

class WindowManager(ScreenManager):
    pass

class ClientApp(App):
    def build(self):
        return Builder.load_file("interface_client.kv")

ClientApp().run()