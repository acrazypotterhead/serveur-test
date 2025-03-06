import socket
import threading
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock
from kivy.lang import Builder
from kivy_garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg
import matplotlib.pyplot as plt
import kivy_matplotlib_widget
from matplotlib import pyplot as plt
from matplotlib.ticker import MaxNLocator
import matplotlib as mpl
import numpy as np

#optimized draw on Agg backend
mpl.rcParams['path.simplify'] = True
mpl.rcParams['path.simplify_threshold'] = 1.0

#depending of the data. This can increase the graph rendering
#see matplotlib doc for more info
#https://matplotlib.org/stable/users/explain/artists/performance.html#splitting-lines-into-smaller-chunks
mpl.rcParams['agg.path.chunksize'] = 1000


# Configuration du serveur

HEADER = 64
PORT = 5050
SERVER = "192.168.5.27"  # Vérifie bien cette adresse IP
ADDR = (SERVER, PORT)
FORMAT = "utf-8"
DISCONNECT_MESSAGE = "!DISCONNECT"

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)

N = 100000
count_index = 0

xdata = np.arange(N)
x = []
y = []
z = []
time = []
max_data_window = 500
ratio_data = 2


class FirstWindow(Screen):

    

    def __init__(self, **kwargs):
        super(FirstWindow, self).__init__(**kwargs)
        self.data_count = 0
        self.count_time = 0
        self.index = -1
     

    def update_status(self, status):
        Clock.schedule_once(lambda dt: self.ids.status_label.setter('text')(self.ids.status_label, status))

    def update_messages(self, message):
        Clock.schedule_once(lambda dt: self.ids.messages.setter('text')(self.ids.messages, self.ids.messages.text + message + "\n"))

    def handle_client(self, conn, addr):
        self.update_status(f"[NEW CONNECTION] {addr} connected.")
        connected = True
        with open("arrays.txt", "a") as f:
            while connected:
                try:
                    msg_length = conn.recv(HEADER).decode(FORMAT)
                    if msg_length:
                        msg_length = int(msg_length)
                        msg = conn.recv(msg_length).decode(FORMAT)

                        
                        split_msg = msg.split(",")
                        if len(split_msg) == 3:
                            x.append(float(split_msg[0]))
                            y.append(float(split_msg[1]))
                            z.append(float(split_msg[2]))

                            self.data_count += 1 
                            
                        

                        f.write(f"{x}\n")
                        f.write(f"{y}\n")
                        f.write(f"{z}\n")
                        


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
        Clock.schedule_interval(self.reset_data_count, 1)
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

    line1 = None
    line2 = None
    line3 = None
    min_index=0
    max_index=1
    current_xmax_refresh=None

    def start_graph(self):
        fig, ax = plt.subplots(1, 1)
        self.line1, = plt.plot([], [],color="green", label = "X")
        self.line2, = plt.plot([], [],color="red", label = "Y")
        self.line3, = plt.plot([], [],color="blue", label = "Z")

        Clock.schedule_interval(self.update_time, 0.08)

        ax.xaxis.set_major_locator(MaxNLocator(prune='lower',nbins=5))

        self.current_xmax_refresh = xdata[max_data_window]

        print(f"de base{self.current_xmax_refresh}")

        xmin = 0
        xmax = self.current_xmax_refresh

        ax.set_xlim(xmin, self.current_xmax_refresh)
        ax.set_ylim(-40, 40)

        self.figure_wgt.figure =fig 
        self.figure_wgt.xmin =xmin 
        self.figure_wgt.xmax = xmax 
        self.home()

        Clock.schedule_once(self.update_graph_delay,3)

    def update_time(self, dt):
        time.append(self.count_time)
        self.count_time += 1
        
    def modulo (self, a):
        mod = divmod(a, max_data_window)
        return mod
    


    def update_graph_delay(self, *args):   
        #update graph data every 1/60 seconds
        Clock.schedule_interval(self.update_graph,1/60)

    def update_graph(self, *args):

        current_x = time[self.min_index:self.max_index]
        current_y1 = x[self.min_index:self.max_index] 
        current_y2 = y[self.min_index:self.max_index] 
        current_y3 = z[self.min_index:self.max_index]
        #print(current_x)
        
        # Assurez-vous que les longueurs des tableaux sont égales
        min_length = min(len(current_x), len(current_y1), len(current_y2), len(current_y3))
        #xdata = xdata[:min_length]
        
        current_x = current_x[:min_length]
        current_y1 = current_y1[:min_length]
        current_y2 = current_y2[:min_length]
        current_y3 = current_y3[:min_length]


        if not self.max_index > N:

            self.line1.set_data(current_x,current_y1)
            self.line2.set_data(current_x,current_y2)
            self.line3.set_data(current_x,current_y3)

            if self.figure_wgt.axes.get_xlim()[0]==self.figure_wgt.xmin:
                if len(current_x) != 0:
                    self.index += 1
                    print(f"index {self.index}")
                    print(f"mod {self.modulo(self.index)}")

                    if 0 == self.modulo(self.index)[0]:           #self.current_xmax_refresh:   

                        myfig=self.figure_wgt
                        ax2=myfig.axes
                        #use blit method            
                        if myfig.background is None:
                            myfig.background_patch_copy.set_visible(True)
                            ax2.figure.canvas.draw_idle()
                            ax2.figure.canvas.flush_events()                   
                            myfig.background = ax2.figure.canvas.copy_from_bbox(ax2.figure.bbox)
                            myfig.background_patch_copy.set_visible(False)  
                        ax2.figure.canvas.restore_region(myfig.background)

                        for line in ax2.lines:
                            ax2.draw_artist(line)
                        ax2.figure.canvas.blit(ax2.bbox)
                        ax2.figure.canvas.flush_events()                     
                    else:
                        #update axis limit
                        
                        try:
                            self.current_xmax_refresh =  time[self.max_index + int( max_data_window -  max_data_window// ratio_data)]
                            
                            print(f"try {self.max_index} ")
                            print(f"try {self.current_xmax_refresh} ")
                        except:
                            self.current_xmax_refresh =  time[-1]
                            print(f"except{self.current_xmax_refresh}")
                        # self.current_xmax_refresh = new_x[max_data_window]
                        self.figure_wgt.xmin = time[self.max_index - int( max_data_window// ratio_data)]
                        self.figure_wgt.xmax =self.current_xmax_refresh 
                        myfig=self.figure_wgt
                        ax2=myfig.axes                     
                        myfig.background_patch_copy.set_visible(True)
                        ax2.figure.canvas.draw_idle()
                        ax2.figure.canvas.flush_events()                   
                        myfig.background = ax2.figure.canvas.copy_from_bbox(ax2.figure.bbox)
                        myfig.background_patch_copy.set_visible(False)           
                        
                        self.home()
            else:
                #minimum xlim as changed. pan or zoom if maybe detected
                #update axis limit stop
                myfig=self.figure_wgt
                ax2=myfig.axes
                #use blit method            
                if myfig.background is None:
                    myfig.background_patch_copy.set_visible(True)
                    ax2.figure.canvas.draw_idle()
                    ax2.figure.canvas.flush_events()                   
                    myfig.background = ax2.figure.canvas.copy_from_bbox(ax2.figure.bbox)
                    myfig.background_patch_copy.set_visible(False)  
                ax2.figure.canvas.restore_region(myfig.background)
               
                for line in ax2.lines:
                    ax2.draw_artist(line)
                ax2.figure.canvas.blit(ax2.bbox)
                ax2.figure.canvas.flush_events()   

            self.max_index+=1 #increase step value (each frame, add 20 data)
            
            #print(f"max_index {time}")
        else:
            Clock.unschedule(self.update_graph)
            myfig=self.figure_wgt          
            myfig.xmin = 0#if double-click, show all data            

    def home(self):
       self.figure_wgt.home()

    def set_touch_mode(self,mode):
        self.figure_wgt.touch_mode=mode

    def reset_data_count(self, dt):
        #print(f"Data per second: {self.data_count}")
        self.data_count = 0  # Réinitialiser le compteur


class SecondWindow(Screen):
    pass


class WindowManager(ScreenManager):
    pass


class ServerApp(App):
    def build(self):
        return Builder.load_file("interface_serveur.kv")


if __name__ == "__main__":
    ServerApp().run()
