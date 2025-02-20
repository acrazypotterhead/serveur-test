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
#SERVER = "192.168.137.248"  # Vérifie bien que cette IP est correcte
#ADDR = (SERVER, PORT)
serveur_ip = ""



class ClientApp(App):
    def build(self):
        if platform == 'android':
            request_android_permissions()
            
        
        layout = GridLayout(cols=1)
        self.label_ip = Label(text="Enter server IP:")
        self.input_ip = TextInput()
        self.button_ip = Button(text="Connect")
        
      
        self.button_ip.bind(on_press=self.set_server_ip)

        self.label_msg = Label(text="Enter a message:")
        self.input_msg = TextInput()
        self.button = Button(text="Send")
        self.button.bind(on_press=self.send_message)

        self.button_gyro = Button(text="Gyroscope")
        self.button_gyro.bind(on_press=self.do_toggle)
        

        
        layout.add_widget(self.label_ip)
        layout.add_widget(self.input_ip)
        layout.add_widget(self.button_ip)
        layout.add_widget(self.label_msg)
        layout.add_widget(self.input_msg)
        layout.add_widget(self.button)
        layout.add_widget(self.button_gyro)


        
        return layout
    
    def start_gyroscope(self, instance):
        threading.Thread(target=self.collect_accelerometer_data).start()

    


    def set_server_ip(self, instance):
        self.serveur_ip = self.input_ip.text  # Store the server IP in an instance variable
        print(f"Server IP set to: {self.serveur_ip}")
        # Start the connection in a new thread to avoid blocking the UI
        threading.Thread(target=self.connect_to_server, args=(self.serveur_ip,)).start()


    
    def connect_to_server(self, serveur_ip):
        while True:
            try:
                self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client.connect((serveur_ip, PORT))
                print("[CONNECTED] Successfully connected to the server")
                break
            except Exception as e:
                print(f"[ERROR] Could not connect to server: {e}")
                self.client = None
                time.sleep(5)

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
        message = self.input_msg.text  # Get the message from the input
        self.send(message)

    sensor = False

    def do_toggle(self):   
        if not self.sensorEnabled:
            try:
                accelerometer.enable()
                print(accelerometer.acceleration)
                self.sensorEnabled = True
                #self.ids.toggle_button.text = "Stop Accelerometer"
            except:
                print("Accelerometer is not implemented for your platform")
    
            if self.sensorEnabled:
                Clock.schedule_interval(self.collect_accelerometer_data, 1 / 20)
            else:
                accelerometer.disable()
                status = "Accelerometer is not implemented for your platform"
                #self.ids.toggle_button.text = status
        else:
            # Stop de la capture
            accelerometer.disable()
            Clock.unschedule(self.get_acceleration)
    
            # Retour à l'état arrété
            self.sensorEnabled = False
            #self.ids.toggle_button.text = "Start Accelerometer"

        
    

    def collect_accelerometer_data(self):
        
        if self.sensor:
            val = accelerometer.acceleration[:3]
            val_x = val[0]
            val_y = val[1]
            val_z = val[2]

            self.send(val_x)


    
        
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

ClientApp().run()